# Data Center Industry Pack - Version 1.2.1

The Data Centers Industry Pack is a collection of resources that provide pre-built, ready to use solutions for data centers. This includes faceplate &amp; UDT pairs for an Uninterruptible Power Supply (UPS) and an Air Handling Unit (AHU).
This pack also includes several widgets, and a dynamic popup for displaying tag names and values.
In addition to faceplates and widgets, a Comtrade resource is also included to import, view and export Comtrade files and data.

## Installation

### Custom Instructions
See attached PDF

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

## Release Notes
Enable Comtrade phasor calculations

## Authors and Acknowledgment
Built for the [Ignition Exchange](https://inductiveautomation.com/exchange) by IA Sales Engineering

## Support
View [Data Center Industry Pack](https://inductiveautomation.com/exchange/2737) for more information, and other [versions](https://inductiveautomation.com/exchange/2737/versions)

## License
+ [MIT](https://choosealicense.com/licenses/mit/)
+ [Terms & Conditions](https://inductiveautomation.com/exchange/terms)
+ [Acceptable Use](https://inductiveautomation.com/exchange/use)
