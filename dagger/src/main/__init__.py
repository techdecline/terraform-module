import dagger
from dagger import dag, function, object_type


@object_type
class TerraformModule:

    @function
    async def terraform_plan(self, directory_arg: dagger.Directory, azauth_directory: dagger.Directory)-> str:
        return await (
            dag.container()
            .from_("devopsinfra/docker-terragrunt:azure-tf-1.7.0-tg-0.54.21")
            .with_mounted_directory("/mnt", directory_arg)
            .with_mounted_directory("/root/.azure", azauth_directory)
            .with_workdir("/mnt/test")
            .with_exec(["terraform", "init"])
            .with_exec(["terraform", "plan"])
            .stdout()
        )

    @function
    async def terraform_checkov(self, directory_arg: dagger.Directory)-> str:
        return await (
            dag.container()
            .from_("bridgecrew/checkov:latest")
            .with_mounted_directory("/mnt", directory_arg)
            .with_workdir("/mnt/test")
            .with_exec(["-d", ".","--quiet","--compact" ])
            .stdout()
        )
    
    @function
    async def terraform_tflint(self, directory_arg: dagger.Directory)-> str:
        return await (
            dag.container()
            .from_("ghcr.io/terraform-linters/tflint")
            .with_mounted_directory("/mnt", directory_arg)
            .with_workdir("/mnt/test")
            # .with_exec(["-d", ".","--quiet","--compact" ])
            .stdout()
        )
    
    @function
    async def terragrunt_test(self, directory_arg: dagger.Directory,azauth_directory: dagger.Directory)-> str:
        return await (
            dag.container()
            .from_("devopsinfra/docker-terragrunt:azure-tf-1.8.0-tg-0.57.0")
            .with_mounted_directory("/mnt", directory_arg)
            .with_mounted_directory("/root/.azure", azauth_directory)
            .with_workdir("mnt/tg_test")
            .with_exec(["go","mod","init"])
            .with_exec(["go","test"])
            .stdout()
        )