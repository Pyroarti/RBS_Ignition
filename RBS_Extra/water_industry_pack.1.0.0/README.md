# Water Industry Pack - Version 1.0.0

The Ignition Water Industry Pack includes a variety of components to quickly build screens that match your operations with water/wastewater-specific components including tanks, pumps, valves, and VFDs.  Each component is paired with a UDT so you can quickly connect live PLC tags and visualize your data.

## Installation

### Custom Instructions
After downloading the resource, unzip the file.
After unzipping the file, open and refer to the Setup section of the Water Industry Pack Guide pdf, which can be found in the folder named Other, for detailed installation instructions.

### Common Instructions

**Project (.zip/.proj)**  
Project backup and restoring from a project backup is referred to as Project Export and Import. Projects are exported individually, and only include project-specific elements visible in the Project Browser in the Ignition Designer. They do not include Gateway resources, like database connections, Tag Providers, Tags, and images. The exported file (.zip or .proj) is used to restore / import a project.

.zip = Ignition 8+
.proj = Ignition 7+

There are two primary ways to export and import a project:

Gateway Webpage - exports and imports the entire project.
Designer -  exports and imports only those resources that are selected.

When you restore / import a project from an exported file in the Gateway Webpage, it will be merged into your existing Gateway.

The import is located in:
Ignition Gateway > Configuration > System > Projects > Import Project Link

If there is a naming collision, you have the option of renaming the project or overwriting the project. Project exports can also be restored / imported in the Designer. Once the Designer is opened you can choose File > Import from the menu. This will even allow you to select which parts of the project import you want to include and will merge them into the currently open project.

**Tags (.json/.xml/.csv)**  
Ignition can export and import Tag configurations to and from the JSON (JavaScript Object Notation) file format. You can import XML (Extensible Markup Language) or CSV (Comma Separated Value) file formats as well, but Ignition will convert them to JSON format. Tag exports are imported in the Designer. Once the Designer is opened you can click on the import button in the Tag Browser panel.

### Requirements

**Modules**

+ Perspective
+ Web Development

## Release Notes
This is the initial release of the Ignition Water Industry Pack.

## Authors and Acknowledgment
Built for the [Ignition Exchange](https://inductiveautomation.com/exchange) by IA Sales Engineering

## Support
View [Water Industry Pack](https://inductiveautomation.com/exchange/2745) for more information, and other [versions](https://inductiveautomation.com/exchange/2745/versions)

## License
+ [MIT](https://choosealicense.com/licenses/mit/)
+ [Terms & Conditions](https://inductiveautomation.com/exchange/terms)
+ [Acceptable Use](https://inductiveautomation.com/exchange/use)
