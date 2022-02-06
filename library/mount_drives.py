from ansible.module_utils.basic import AnsibleModule
from subprocess import run, PIPE
import re

def shell_command(cmd):
    command = cmd.split()
    result = run(command, stdout=PIPE)
    return result.stdout.decode('utf8').split("\n")

def shell_command_rc(cmd):
    command = cmd.split()
    result = run(command, stdout=PIPE, stderr=PIPE)
    return result.returncode

def get_available_devices(ignore_devs):
    regex = []
    for x in ignore_devs:
        regex.append(".*" + x + ".*")
    ignore_pattern = re.compile("|".join(regex))

    stdout_lines = shell_command("sudo blkid -o device")
    target_devices = []
    for line in stdout_lines:
        if not ignore_pattern.match(line) and line != "":
            target_devices.append(line.replace("/dev/",""))
    return target_devices

def device_mapping(devices):
    pattern = re.compile('(' + '|'.join(devices) + ')')
    stdout_lines = shell_command(f"sudo lsblk -lno NAME,MOUNTPOINT")
    mappings = []
    for line in stdout_lines:
        if pattern.match(line):
            split_str = line.split()
            dev = '/dev/' + split_str[0]
            if len(split_str) == 2:
                mount = split_str[1]
            else:
                mount = ""
            mappings.append({'device': dev, 'mountpoint': mount})
    return mappings

def assign_needed_mounts(mappings, mountpoints):
    unmounted_devices = []
    already_mounted = set([])
    for x in mappings:
        if x['mountpoint'] != '':
            already_mounted.add(x['mountpoint'])
        else:
            unmounted_devices.append(x['device'])
    
    needed_mounts = list(set(mountpoints).difference(already_mounted))
    assignments = []
    for i, dev in enumerate(unmounted_devices):
        assignments.append({'device': dev, 'mountpoint':needed_mounts[i]})

    return assignments

def main():
    module = AnsibleModule(
        argument_spec   = dict(
            mountpoints = dict(required=True, type='list'),
            ignore_devs = dict(default=["mmcblk", "loop"], type='list')
        )
    )
    mountpoints = module.params['mountpoints']
    ignore_devs = module.params['ignore_devs']
    available_devices = get_available_devices(ignore_devs)

    for path in mountpoints:
        _ = shell_command_rc(f"sudo mkdir -p {path}")

    if len(available_devices) != len(mountpoints):
        error_msg = f"The number of desired mountpoints ({len(mountpoints)}) does not equal the number of available devices ({len(available_devices)}). Available: {available_devices}."
        module.fail_json(msg=error_msg)
    else:
        current_mappings = device_mapping(available_devices)
        assigned_mountings = assign_needed_mounts(current_mappings, mountpoints)
        total_mountings = current_mappings.append(assigned_mountings)
        change_flag = False
        for assignment in assigned_mountings:
            cmd = f"sudo mount {assignment['device']} {assignment['mountpoint']}"
            rc = shell_command_rc(cmd)
            if rc != 0:
                error_msg = f"failed to mount {assignment['device']} to {assignment['mountpoint']}"
                module.fail_json(msg=error_msg)
            else:
                change_flag = True
        post_mappings = device_mapping(available_devices)
        module.exit_json(changed=change_flag, devices=post_mappings)




if __name__ == "__main__":
    main()