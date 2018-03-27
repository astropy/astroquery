Red MSX Source service - Multi-wavelength Search for Massive Young Stellar Objects

I've been parsing the HTML of The RMS Cone Search and the RMS Database Search Page. I've outlined the steps to implement the Red MSX Source service. I'll upload the code shortly but I would like feedback on the outline to define specific tasklist. 

1.- Create a main class with two main methods
	
	- rms_search_page
	- rms_cone_search

	1.1 "rms_search_page"

		Required HTML tag/element for a general search of database objects 
			- source_type  <select ; {"name":"source_type"}>
			- submit       <input ; {"type":"submit"}>

		Tags/elements for specific searches

			All rows with specific search parameters have four elements

				-  <select ; {"name":"equality_?"}>
				-  <input  ; {"name":"lower_?", "type": "input"} >
				-  <input  ; {"name":"upper_?", "type": "input"}>
				-  <input  ; {"name":"checkbox_msx_?", "type": "checkbox"}>

			where "?" refers to specific  "id" by row

			With "Include Near/Far Distance" as the only exception

			All rows are grouped by two categories: 

				- Group with "Include Nulls" option
				- Group without "Include Nulls" option

		If the user doesn't want more detailed results, the page provides an option to download a csv file separated by tab with all records for the search "Create Text Output File" <input ; {"name":"output", "type":"radio"}>. 

		STEPS:
			- Create the main method to "rms_search_page" that allows the user to choose the inputs for a specific search
			- Create a secondary method that separates between "Includ Nulls" and "Not Includ Nulls"

	1.2 "rsn_cone_search"

		The search admits three parameters:
			- "Source name or coordinate" <input ; {"name":"text_field_1","type":"text"}>
			- "Search radius" <input ; {"name":"radius_field","type":"text"}>
			- "Options" <input ; {"name":"listID", "type":"radio"}>
		And submit button
			- submit       <input ; {"type":"submit"}>

		The results for an object are shown in several HTML tables that can be separated in two classes:

			- With images
			- Text only
		In "With images" class the datasets are in the figure caption in the "a" element.  For the "text only" class the info is in HTML tables. 

		STEPS: 
			- Create the main method to "rsn_cone_search" that allows the user to input field values 
			- Create a main method to "return_results_rms" that allows to choose the format and files to show/download
			- Create a method that allows to separate the results tables in two classes
			- Create a method to read "text only" results 
			- Create a method to download the .fits archives












