Governance, Risk and Compliance (GGRC)
=========

[![Build Status](https://jenkins.reciprocitylabs.com/job/ggrc_develop_build/badge/icon)](https://jenkins.reciprocitylabs.com/job/ggrc_develop_build/)

Governance, Risk Management, and Compliance are activities necessary for any organization with regulatory or contractual obligations.

Governance refers to management structure, policies, procedures, shareholder relations, etc.

Risk Management is a process to identify business and technical risks as well as means to mitigate those.

Compliance refers to processes necessary to meet applicable regulations and communicate to stakeholders about it.

Many organizations operate in multiple jurisdictions worldwide, each of which has its own and often overlapping laws and regulations.   Organizational functions and information relating to risk management and compliance often tend to be managed in silos reflecting the multiple jurisdictions, scope, stakeholder diversity and historical basis.   This leads to inefficiency.

The GGRC project intends to provide an open source solution for managing some of these common problems.  The application provides a common system of record for information in this domain.   It provides the ability to capture the relationships and to understand how the pieces fit together.  It also provides workflow capability to manage processes in this domain.


Migrated from [Google](https://code.google.com/archive/p/compliance-management)
[Code](https://code.google.com/archive/p/ggrc-core).


## Requirements

The following software is required to stand up a GGRC-Core development
environment:

|               Prerequisite                       |                 Description              |
|--------------------------------------------------|------------------------------------------|
|[Docker](https://www.docker.com/)                 | Container management tool                |
|[Docker compose](https://docs.docker.com/compose/)| A tool for defining multi-container apps |

**NOTE for Windows/OSX users:** The easiest way of getting docker is by installing the
[docker toolbox](https://www.docker.com/products/docker-toolbox).

Or alternatively with our legacy vagrant environment:

|               Prerequisite               |               Description                |
|------------------------------------------|------------------------------------------|
|[VirtualBox](https://www.virtualbox.org/) | Oracle VirtualBox Virtual Machine player |
|[Vagrant](https://www.vagrantup.com/)      | Handy scriptable VM management           |
|[Ansible](https://www.ansible.com/)    | Provisioning and deployment tool         |

## Quick Start with Docker

Getting started with GGRC-Core development should be fast and easy once you
have docker up and running. Here are the steps:

**NOTE for Windows/OSX users:** Make sure `docker` is up and running by following the [windows guide](https://docs.docker.com/engine/installation/windows/#using-docker-from-windows-command-prompt-cmd-exe) / [osx guide](https://docs.docker.com/engine/installation/mac/#from-your-shell).

* clone the repo
* cd to the project
directory
* run the following:

    ```
    git submodule update --init
    docker-compose up -d
    docker exec -it ggrccore_dev_1 su vagrant
    make -B bower_components
    build_css
    build_assets
    db_reset
    ```

If you see download errors during the `docker-compose up -d` stage, or if any subsequent
step fails, try running `docker-compose build` (See [Reprovisioning a Docker container](#reprovisioning-a-docker-container) below for more).

_NOTE: Because docker shared volumes do not have permission mappings, you should run these commands as a user with UID 1000, to match the users inside the containers._

## Quick Start with Vagrant (legacy)

Alternative setup is using vagrant

* clone the repo
* cd to the project directory
* make sure you use ansible version 1.9.X (if it's not in the repositories, you can
install it via pip)
* run the following:

    ```sh
    git submodule update --init
    vagrant up
    vagrant ssh
    build_css
    build_assets
    db_reset
    ```

If you see download errors during the `vagrant up` stage, or if any subsequent
step fails, try running `vagrant provision` (See [Provision a running Vagrant
VM](#provision-a-running-vagrant-vm) below for more).

Now you're in the VM and ready to rock. Get to work!


### Launching GGRC as Stand-alone Flask

Most development is done in a stand-alone flask. We strive to make getting up
and running as simple as possible; to that end, launching the application is
simple:

```sh
launch_ggrc
```

### Launching GGRC in Google App Engine SDK

We strive to make getting up and running as simple as possible; to that end,
launching the application in the Google App Engine SDK environment is simple:

```sh
launch_gae_ggrc
```

This requires `src/app.yaml` and `src/packages.zip` with settings. You can generate the yaml file with:

```sh
deploy_appengine extras/deploy_settings_local.sh
```

And the packages.zip file with:


```
make appengine_packages_zip
```



### Accessing the Application

The application will be accessible via this URL: <http://localhost:8080/>

If you're running the Google App Engine SDK, the App Engine management console
will be available via this URL: <http://localhost:8000/>. You can login as
user@example.com with admin rights and setup other users later.

## Running Tests

Tests are your friend! Keep them running, keep them updated.

#### For JavaScript tests:

```sh
run_karma # To run karma with PhantomJS
run_karma_chrome # To run karma in host browser (open http://localhost:9876)
```

`run_karma` is the default way of running tests as it automatically
builds the javascript assets on file changes. Use `run_karma_chrome` if you
need to debug an issue in the chrome browser. For performance reasons
`run_karma_chrome` does not automatically build assets, so make sure you do it
manually by running `build_assets`.

#### For Python tests:

```sh
run_pytests
```

The script will run unit tests and integration tests.

For better usage of unit tests you can use sniffer inside the test/unit folder.
This will run the tests on each file update.

```sh
cd test/unit; sniffer
```

You can drop into ipdb debugger on failures by running:

```sh
run_pytests --ipdb-failures
```

#### For Selenium tests:

On the host machine in the root of the repository run:

```sh
./bin/jenkins/run_selenium
```

##### Manually running selenium tests

For selenium tests, you must use the docker environment. There are two containers needed for running seleium tests `ggrccore_dev_1` and `ggrccore_selenium_1`. Due to a bug in the selenium container, you must start the containers with:

```
docker-compose  up -d --force-recreate
```
After that you can make sure that both containers are running with `docker ps -a`.

To run the selenium tests, you must login into your dev container, and run the server:
```
docker exec -it ggrccore_dev_1 su vagrant
make bower_components
build_css
build_assets
db_reset
launch_ggrc
```

Then you can login into the selenium container and run the tests:

```
docker exec -it ggrccore_selenium_1 bash
python /selenium/src/run_selenium.py
```

You should also feel free to check how the `./bin/jenkins/run_selenium` script works.

_NOTE: that the "ggrccore" part of the name is due to the repository parent folder name. if you have your repo in a different folder, change the first part accordingly._


## Quickstart Breakdown


The quickstart above gives a glimpse into the GGRC development environment.
It's worth noting where there is automation in GGRC, and where there isn't.
Often the lack of automation support for a step is intentional. Let's explore
each step in detail.

### Git Submodules in GGRC

GGRC makes use of some external tools for [Sass](http://sass-lang.com/)
templates and JavaScript form handling. In order to have the relevant
repositories checked out as Git submodules the following command must be
issued in the project directory:

```sh
git submodule update --init
```

### Ansible

GGRC-Core provides both a `Vagrantfile` and an Ansible playbook to make
standing up a development environment simple and repeatable thanks to the magic
of Vagrant and Ansible. Vagrant enables developers to use a consistent and
shared VM configuration to perform application testing while allowing
developers to use the source code editing environment of their choice.

### Vagrant

The application is run in a virtual machine environment that can be repeatably,
consistently, and reliably constructed thanks to Vagrant. In order to use
Vagrant to create and manage the development virtual machine environment, it
must first be created by issuing the following command from the project
directory:

```sh
vagrant up
```

This results in the creation of the virtual machine and the provisioning of
required software to support the development and execution of GGRC.

#### Reprovisioning a Vagrant VM

There are several ways to update the provisioning of a Vagrant VM when changes
have been made to the cookbooks or other dependency management mechanisms in
GGRC.

##### Provision a running Vagrant VM

To run provisioning on a running Vagrant VM, simply run the following in the
project directory:

```sh
vagrant provision
```

##### Provisioning a halted Vagrant VM

If you have halted your Vagrant VM via `vagrant halt`, simply `vagrant up`
in the project directory to have provisioning run and update your development
environment.

##### Clean Slate Provisioning

To create a clean slate environment in your Vagrant VM you can either reload or
recreate the environment. To reload the environment issue the following command
in the project directory:

```sh
vagrant reload
```

To completely recreate the environment issue the following command in the
project directory:

```sh
vagrant destroy
vagrant up
```

#### Reprovisioning a Docker container

To reprovision a docker container run the following:

Remove files that are not in the repository e.g. python cache:
```sh
git clean -df
```
Start reprovisioning:
```sh
docker-compose build --pull --no-cache
```

Because docker provisioning is done with Dockerfile which can not modify content of a shared volume, you need to enter the container and run one more step to finish the provisioning

```
docker-compose up -d --force-recreate
docker exec -it ggrccore_dev_1 su vagrant
make bower_components
```


### Compiling Sass Templates

Since GGRC uses Sass for CSS templating, the templates need to be compiled.
This has been automated via a script available in $PATH in the virtual
machine:

```sh
build_css
```

To have a process watch the Sass resources and compile them as they are changed
you could use this command:

```sh
watch_css
```

### Compiling Assets

For other asset bundling required, there is the following command:

```sh
build_assets
```

As for CSS, there is an asset builder that can watch for changes and update
files as they change:

```sh
watch_assets
```

### Importing Example Data

Example test data can be loaded with the following command:

```sh
db_reset backup-file.sql
```

## Gotchas

After sync'ing your local clone of GGRC-Core you may experience a failure when
trying to run the application due to a change (usually an addition) to the
prerequisites.

There are three primary classes of requirements for GGRC-Core: Submodules, Python requirements and other provision steps

There are two pip requirements files: a runtime requirements file,
`src/requirements.txt`, for application package dependencies and a
development requirements file, `src/requirements-dev.txt`, for additional
development-time package dependencies. The runtime requirements are deployed
with the application while the development requirements are only used in the
development environment (largely for testing purposes).

Most requirements changes should be in either `src/requirements.txt` or
`src/requirements-dev.txt` and would manifest as module import failures.

### Environment Variables

*GGRC_SETTINGS_MODULE*:

GGRC uses this environment variable to define which module(s) within
`ggrc.settings` to use during the bootstrap phase. The value can be one
or more space-separated module names, which will be applied in the same
order they are specified. `source bin/init_env` will set this value to
`development`.

### Details About VM File Structure

`vagrant provision` installs several Debian packages globally within the
VM. All other project data is contained within two directories, specified by
environment variables (and defined in `/home/vagrant/.bashrc`).

*PREFIX*:

Points at root directory of the Git repository, and is automatically
detected if not present.

*DEV_PREFIX*:

Points at a directory containing `tmp` and `opt` directories. If not
defined, `DEV_PREFIX` defaults to the value of `PREFIX`. (In the VM,
it is defined to `/vagrant-dev` to avoid slowdown caused by the shared
filesystem at `/vagrant`.)

### Changes to Requirements Files

The first thing to try to resolve issues due to missing prerequisites is to
run the following command from within the project directory in the host
operating system:

```sh
vagrant provision
```

or if you're using docker:

```sh
docker-compose build
```


This will prompt vagrant to run the Ansible provisioner or docker to rebuild the containers. The result of this
command *should* be an update Python virtualenv containing the Python packages
required by the application as well as any new development package
requirements.

To Manually update the requirements, you can login to vagrant or docker virtual machine and run

```sh
pip install -r src/requirements-dev.txt
pip install --no-deps -r src/requirements-basic.txt
```

Note that if you're using `launch_gae_ggrc`, then changes to
`src/requirements.txt` will require rebuilding the `src/packages.zip` via

```
make appengine_packages_zip
```


### Git Submodule Changes

A change in the git submodules required by the project could also lead to
errors, particularly in the front-end HTML portion of the application. The
solution is to update the submodules:

```sh
git submodule update
```

Given that Sass and Javascript related projects are included in the submodule
requirements of GGRC, it may also be necessary to rebuild the Sass and other
web assets:

```sh
build_css
build_assets
```

# Copyright Notice

Copyright (C) 2013-2017 Google Inc., authors, and contributors (see the AUTHORS
file).
Licensed under the [Apache 2.0](http://www.apache.org/licenses/LICENSE-2.0)
license (see the LICENSE file).
