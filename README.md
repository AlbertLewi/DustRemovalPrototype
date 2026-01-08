# Dust Removal Prototype
This program is a prototype for a dust removal pipeline I am working on for a project. The given pipeline uses a variety of OpenCV2 based methods and has many limitations to explore and fix. Arduino integration for lux detection can be used but is not required, code will still run. Test images are included. 
- 6 Step Processing pipeline with limitations
- Image names must be manually changed
- Path for run image storge must be specified by you
- Detection works fairly well within the limitations
- Make your own test folders and what not 

Some Limitations:
- Code can not handle reflections on dust just reflections on surrounding surfaces
- Code can not handle other intefering objects on surface
- Surface must be quite flat
- Small films of dust may be missed
- Code does not discriminate between dust and other objects
- Code can not handle live imaging
- Code can not auto determine accuracy, accuracy must be empirically tested, which is possible with the given test images

Current Use:
- Code can handle flat clear surface images with semi large dust particles and more obvious dust films
- Code can handle a variaty of backgrounds
- Code can handle large reflections on glass background or other reflective backgrounds
- Code can calculate dust to surface coverage ratio
- Code can auto organize data along with lux in a CSV file
- Code is light weight and runs quickly 
