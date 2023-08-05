# OPCUA-AsyncIO Build Pipelines

The `opcua-asyncio` build pipeline repository is intended to provide flexible and configurable pipelines for different CI/CD platforms such as Github Actions, GitLab, Tekton, and Azure DevOps. The aim is to make the integration process easier and facilitate custom script creation by users.

## Overview

`opcua-asyncio` is an asyncio-based asynchronous OPC UA client and server based on `python-opcua`, eliminating support of python < 3.7. It provides a simple, efficient, and powerful way to write a server or a client using both low-level and high-level UA calls.

With this build pipeline repository, you can easily integrate your `opcua-asyncio` project with your favorite CI/CD platform and enjoy the power of automated build, test, and deployment.

## Usage

To use the build pipelines repository:

1. Clone this repository.

```bash
git clone https://github.com/yourusername/opcua-asyncio-build-pipelines.git
```

2. Navigate to the directory corresponding to the CI/CD platform you want to use (Github Actions, GitLab, Tekton, or Azure DevOps).

3. Create your build script and place it in the directory.

4. Configure the pipeline settings according to your CI/CD platform's documentation and your project requirements.

## Custom Scripts

Users have the ability to create their custom scripts for the build pipeline. After creating your script, put it in the respective CI/CD platform's directory. The pipeline will build it as part of its process.

## Contributing

Contributions to the `opcua-asyncio` build pipeline repository are welcome and greatly appreciated. Please ensure to follow the existing directory structure while adding new scripts or modifying the existing ones.

## Support

For any issues, queries, or assistance, please raise an issue in the repository. We will try to address it as soon as possible.

## License

The `opcua-asyncio` build pipelines repository is open-source and is licensed under the MIT License. Please see the [LICENSE](./LICENSE) file for details.

Note: The usage of the `opcua-asyncio` library must abide by its respective licensing terms.

---

This README provides the basic instructions to get started with the `opcua-asyncio` build pipelines repository. Depending on the specific configurations and requirements of your project and chosen CI/CD platform, you may need to consult their respective documentation or community for more detailed instructions or troubleshooting.