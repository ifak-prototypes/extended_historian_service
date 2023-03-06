# Extended Historian Service for the Arrowhead Framework

Modern automation solutions in industrial production often integrate several communication solutions. This applies to classic control systems as well as modern IIoT solutions and systems of systems, such as the Eclipse Arrowhead Framework (<https://projects.eclipse.org/projects/iot.arrowhead>). The Extended Historian Service supplements the basic functions of the Arrowhead Framework with the possibility of cyclical and centrally controlled collection of data (time series). The software in this repository includes an implementation of the core components of the Extended Historian Service as well as sample code for devices and data analysis applications.

## Installation

We assume that you are using a Linux system. Here you need to checkout the repository and open a terminal window in the root directory of the checked out repository. Here you can do the following to create a virtual Python environment and install the necessary libraries.

```
bash ./bin/prepare.sh
```

## Example demonstration

To get this system-of-system up and running, several services need to be started. There is a small command line interface to start the services:

```
bash ./bin/demo.sh
```

Type "help" to get some hints on which commands can be used. For getting the demonstration running, we need to start-up the following services:

* Arrowhead System (starts several docker containers: MySQL, Arrowhead Service Registry, Orchestrator and Authentication)
*  XML RPC device
* Arrowhead device
* XML RPC adapter
* Arrowhead adapter
* EHS (the Extended Historian Service core system)
* Application (a demo application including a diagram plot)

## Extending the software

Visual Studio Code (<https://code.visualstudio.com/>) has been used for software development. Start-up scripts have been added in the launch.json file in the .vscode folder.

If you change the interfaces of the EHS then you need to modify the .proto files in the ./src/ehs/api folder. After each change, you need to run:

```
bash ./bin/generate.sh
```

## Trouble shooting

By default, the newest libraries are used. They could be newer, than the source code in this repository, which has potential incompatibilities. In this case, you have to create a Python virtual environment by yourself and after activating it, you need to run:

```
python -m pip install  -r requirements.txt
```

## Acknowledgements

The research work leading to these results has received grants as project Arrowhead Tools from the European H2020 research and innovation programme and the ECSEL Joint Undertaking under grant agreement no. 82645 as well as from the German Federal Ministry of Education and Research (FKZ 16ESE0359). We are grateful to have been given that opportunity for our research activities.

## References

An article is available about the why, what and how of this tool: Thron, M.; Bangemann, Th.: Data Acquisition for the Arrowhead Framework. Materials, Methods and Technologies, 24th International Conference, 19-22 August 2022, Burgas, Bulgaria, online: <https://www.scientific-publications.net/en/article/1002509/> , zuletzt abgerufen am 01.03.2023.

## Copyright and License Information

Copyright (c) 2023, Institut für Automation und Kommunikation e.V. (ifak e.V.).

See the LICENSE file for licensing conditions (MIT license).
