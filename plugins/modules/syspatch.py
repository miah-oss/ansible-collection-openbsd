# SPDX-License-Identifier: ISC
#
# Copyright (c) 2022 Johnathan C. Maudlin <jcmdln@gmail.com>

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


class Syspatch:
    def __init__(self, module: AnsibleModule) -> None:
        self.module: AnsibleModule = module

        # Return values
        self.changed: bool = False
        self.command: str = "/usr/sbin/syspatch"
        self.msg: str = ""
        self.rc: int = 0
        self.reboot: bool = False
        self.stdout: str = ""
        self.stderr: str = ""

    def Apply(self) -> None:
        self.rc, self.stdout, self.stderr = self.module.run_command(self.command, check_rc=False)

        if self.rc == 2 or (not self.stdout and not self.stderr):
            self.msg = "no action performed"
            self.rc = 0
            return

        if self.rc != 0:
            self.msg = "received a non-zero exit code"
            return

        if "reboot" in self.stdout.lower():
            self.reboot = True

        self.changed = True
        self.msg = "patches applied"

    def List(self) -> None:
        if self.module.params["List"].lower() == "available":
            self.command = "{} -c".format(self.command)

        if self.module.params["List"].lower() == "installed":
            self.command = "{} -l".format(self.command)

        self.rc, self.stdout, self.stderr = self.module.run_command(self.command, check_rc=False)

        if self.rc != 0:
            self.msg = "received a non-zero exit code"
            return

        if not self.stdout and not self.stderr:
            self.msg = "no patches to list"
            return

        self.msg = "list of available patches returned"

    def Revert(self) -> None:
        if self.module.params["list"] == "all":
            self.command = "{} -R".format(self.command)

        if self.module.params["list"] == "latest":
            self.command = "{} -r".format(self.command)

        self.rc, self.stdout, self.stderr = self.module.run_command(self.command, check_rc=False)

        if self.rc != 0:
            self.msg = "received a non-zero exit code"
            return

        if not self.stdout and not self.stderr:
            self.msg = "no patches to revert"
            return

        if "reboot" in self.stdout.lower():
            self.reboot = True

        self.changed = True
        self.msg = "patches reverted"


def main() -> None:
    module: AnsibleModule = AnsibleModule(
        argument_spec={
            "apply": {"type": "bool"},
            "list": {"choices": ["available", "installed"], "type": "str"},
            "reboot": {"type": "bool"},
            "revert": {"choices": ["all", "latest"], "type": "str"},
        },
        required_one_of=[["apply", "list", "revert"]],
        mutually_exclusive=[["apply", "list", "revert"]],
        supports_check_mode=False,
    )

    syspatch: Syspatch = Syspatch(module)

    if module.params["apply"]:
        syspatch.Apply()
    elif module.params["list"]:
        syspatch.List()
    elif module.params["revert"]:
        syspatch.Revert()

    result: dict[str, bool | int | str] = {
        "changed": syspatch.changed,
        "command": syspatch.command,
        "msg": syspatch.msg,
        "rc": syspatch.rc,
        "reboot": syspatch.reboot,
        "stdout": syspatch.stdout,
        "stderr": syspatch.stderr,
    }

    if syspatch.rc > 0:
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
