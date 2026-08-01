import os
import tkinter as tk
from tkinter import filedialog
import fitz as f
from PIL import Image

from google import genai
from google.genai import types
from google.genai.errors import APIError

import time
from dotenv import load_dotenv


output_name = "latex_transcrition.tex"
usable_models = {
    "gemini-3.6-flash": True, 
    "gemini-3.5-flash": True,
    "gemini-3.5-flash-lite": True, 
    "gemini-3.1-flash-lite": True
}

load_dotenv()
style_path = os.getenv("STYLE_PATH")
pdf_path = os.getenv("PDF_EXAMPLE")
tex_path = os.getenv("TEX_EXAMPLE")
api_key = os.getenv("GEMINI_API_KEY")

root = tk.Tk()
root.withdraw()

def func(file_name: str, page_number: int):

    page = doc.load_page(page_number - 1)
    graphics = page.get_pixmap(dpi=300)
    temp_image_path = "temp.png"
    graphics.save(temp_image_path)

    # Reading the example files
    testo_stile = open(style_path, "r", encoding="utf-8").read()
    testo_esempio = open(tex_path, "r", encoding="utf-8").read()

    # Deligning instructions as it was a Gem, specializing the response into being what we want
    system_instruction = f"""
    Sei un trascrittore esperto di documenti matematici in LaTeX.
    Il tuo compito è convertire l'image di appunti scritti a mano in codice LaTeX pulito, compilabile e rigoroso.

    DEVI rispettare tassativamente gli ambienti custom, i pacchetti e lo stile definiti nel seguente file .sty:
    --- start STILE_APPUNTI.STY ---
    {testo_stile}
    --- end STILE_APPUNTI.STY ---

    Ecco un esempio di file .tex già strutturato secondo le mie preferenze:
    --- start ESEMPIO.TEX ---
    {testo_esempio}
    --- end ESEMPIO.TEX ---

    REGOLE TASSATIVE:
    1. Rispondi ESCLUSIVAMENTE con il codice LaTeX corrispondente al contenuto dell'image.
    2. Non aggiungere introduzioni, spiegazioni, saluti né blocchi di testo extra.
    3. Se usi delimitatori di codice markdown (es. ```latex), fornisci solo il codice al loro interno.
    4. Non generare il preambolo, non includere documentclass né begin document o end document. 
    Genera ESCLUSIVAMENTE il codice relativo ai capitoli/sezioni presenti nell'image, 
    assumendo che i pacchetti e gli ambienti siano già stati caricati nel documento padre.
    5. Ometti TASSATIVAMENTE gli esercizi quando scritti e gli esempi lasciane al massimo uno,
       ma anche in quel caso cerca di ridurli il più possibile salvo esempi davvero importanti.
    6. Nonostante tu debba ciecamente rispettare ogni singola parola delle immagini di input, voglio che comunque
       tu mantenga una certa formalità, ad esempio limitando il più possibile il grassetto alle cose essenziali, 
       non utilizzando mai il caps lock nonostante nell'image sia utilizzato (devi rendere la dispensa professionale,
       quella scritta su carta è un conto ma su latex ha un altro impatto).
    7. Per la matematica, salvo formule molto importanti, cerca di scriverla per quanto possibile inline. Usa la matematica
       centrata solo quando sono formule davvero importanti ed essenziali del campo dell'analisi.
    8. Fai forte ed estremamente riferimento alla dispensa di analisi caricata come esempio: devi seguire a pieno
       lo stile di quanto ci fosse già scritto, in modo che la continuazione di tutto sembri naturale, scritta dalla stessa persona.
       Dunque mantieni anche gli stili di indentazione e di uso di grassetti e corsivi.
    """

    user_prompt = "Trascrivi fedelmente ed interamente il contenuto di questa page in codice LaTeX."

    # Loading the image we have to send Gemini for it to traduce it
    image = Image.open(temp_image_path)

    # Initializing Gemini: the API Key gets loaded from the system environment variables
    client = genai.Client()

    for model, status in usable_models.items():

        if not status:
            print(f"model {model} not active, skipping")
            continue

        print(f"trying model: {model}\n")
        try:
            # Sending the prompt and saving the answer
            response = client.models.generate_content(
                model=model,
                contents=[image, user_prompt, pdf_path],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                )
            )
            
            # If no error has occured, we can exit the loop and proceed with
            # the writing on the file
            break
        except APIError as e:
            error_msg = str(e)

            # If one of these two strings are in the error message, it means that
            # the RPD limit has been exceeded, meaning that the current model
            # will not be able to be used for the entire day.

            # Else, it probably means that there was an error of connection or the RPM/TPM limit
            # was excedeed: in that case we do nothing since it's a limit that gets resetted way before
            # the RPD one
            if "RESOURCE_EXHAUSTED" in error_msg or "Quota excedeed" in error_msg:
                print(f"model {model} deactivated for the day")
                usable_models[model] = False

    latex_code = response.text

    # To remove occurrences of markdown text left from the Gemini reposnse
    if latex_code.startswith("```"):
        rows = latex_code.splitlines()
        if rows[0].startswith("```"):
            rows = rows[1:]
        if rows and rows[-1].startswith("```"):
            rows = rows[:-1]
        latex_code = "\n".join(rows)

    # Saving the response (that basically contains only latex code)
    # into a file that will progressively contain all of the info
    with open(output_name, "a", encoding="utf-8") as f_out:
        f_out.write("\n% --- NEW PAGE ---\n\n" + latex_code)

    if os.path.exists(temp_image_path):
        os.remove(temp_image_path)


file_name = ""
while (not file_name):
    file_name = filedialog.askopenfilename(
        title="Select the Notes PDF",
        filetypes=[("PDF Files", "*.pdf")]
    )

doc = f.open(file_name)

start = int(input("Starting page: "))
end = int(input("Ending page: "))
print()
end = min(end, len(doc))

total_number_of_pages = (end - start) + 1
before_starting = time.perf_counter()

for i in range(start, end+1):

    before_func = time.perf_counter()

    # Priting just to track where we at
    print(f"page: {i - start + 1}")
    
    func(file_name, i)

    after_func = time.perf_counter()

    print(f"time required for page {i}: {after_func - before_func:.2f} seconds")

    # Waiting 5 seconds not to consume all the RPM tokens
    time.sleep(5)

after_finishing = time.perf_counter()
print(f"total time required for {total_number_of_pages} pages: {after_finishing - before_starting:.2f} seconds")