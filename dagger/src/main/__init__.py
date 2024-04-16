import requests
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
    async def terragrunt_test(self, directory_arg: dagger.Directory,azauth_directory: dagger.Directory)-> dagger.Container:
        azurermProviderVersions = ["3.98.00", "2.47.0"]
        return await (
            dag.container()
            .from_("devopsinfra/docker-terragrunt:azure-tf-1.8.0-tg-0.57.0")
            .with_env_variable("TG_AZURERM_PROVIDER_VERSION","3.98.0")
            .with_mounted_directory("/mnt", directory_arg)
            .with_mounted_directory("/root/.azure", azauth_directory)
            .with_workdir("/mnt/tg_test")
            # .with_exec(["go","mod","init","terratest"])
            # .with_exec(["go","mod","tidy"])
            # .with_exec(["go","test"])
            # .stdout()
        )
        
    @function
    def get_latest_provider_version(provider_name):
        # Construct the URL for the provider on the Terraform Registry
        url = f"https://registry.terraform.io/v1/providers/{provider_name}/versions"

        try:
            # Send a GET request to the Terraform Registry
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the JSON response
                data = response.json()
                # Sort versions in descending order
                sorted_versions = sorted(data['versions'], key=lambda x: x['version'], reverse=True)
                # Extract the latest version from the response
                latest_version = sorted_versions[0]['version']
                return latest_version
            else:
                # If the request was not successful, print an error message
                print(f"Error: Unable to fetch provider version. Status code: {response.status_code}")
                return None
        except Exception as e:
            # If an exception occurs during the request, print an error message
            print(f"Error: {e}")
            return None

    
    @function
    async def terragrunt_test(self, directory_arg: dagger.Directory,azauth_directory: dagger.Directory, azure_rm_provider_version="latest")-> str:
        if azure_rm_provider_version == "latest":
            # Use latest Provider Version
            azure_rm_provider_version = get_latest_provider_version("hashicorp/azurerm")
        return await (
            dag.container()
            .from_("devopsinfra/docker-terragrunt:azure-tf-1.8.0-tg-0.57.0")
            .with_env_variable("TG_AZURERM_PROVIDER_VERSION",azure_rm_provider_version)
            .with_mounted_directory("/mnt", directory_arg)
            .with_mounted_directory("/root/.azure", azauth_directory)
            .with_workdir("/mnt/tg_test")
            .with_exec(["go","mod","init","terratest"])
            .with_exec(["go","mod","tidy"])
            .with_exec(["go","test"])
            .stdout()
        )