## What does this do?
This project, or better this single .py file, essentially operates in the following steps:
1. Lets the user choose a .pdf file which he wants to convert in LaTex.
2. Once the user has chosen the file, it lets him write the starting and ending page of the conversion.
3. For every page, the program temporarely saves it as a png file, then sends a prompt to the Gemini API with such image and three files in which is described the style that the conversion must follow.
4. The page gets converted and its LaTex content gets appended to a .tex file.
5. Rinse and repeat for the number of pages decided.