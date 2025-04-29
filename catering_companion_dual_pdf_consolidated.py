import streamlit as st
import pandas as pd
import random
import time
from fpdf import FPDF
import tempfile

# Kitchen affirmations
affirmations = [
    "You're going to have a great event today!",
    "September is coming. Rest is near!",
    "You're doing great work, keep pushing.",
    "Big events start with small prep wins.",
    "Your mise en place is your superpower.",
    "Stay sharp. Stay strong. Stay caffeinated ☕️.",
    "Organization is the secret ingredient.",
    "The guests won't know, but your team will. Great work!",
    "Good prep saves lives (and lunch rushes).",
    "Every tray you prep is a step closer to success.",
    "Take pride in every tray, every plate, every garnish.",
    "Today's prep is tomorrow's peace.",
    "Keep those knives sharp and your spirits sharper."
]

def scale_recipe(recipe_df, number_of_guests):
    base_servings = recipe_df["BaseServings"].iloc[0]
    scale_factor = number_of_guests / base_servings
    recipe_df["ScaledQuantity"] = recipe_df["Quantity"] * scale_factor
    return recipe_df

def format_shopping_list(scaled_df):
    sections = {}
    grouped = scaled_df.groupby(["Category"])
    for category, group in grouped:
        lines = []
        for _, row in group.sort_values("Ingredient").iterrows():
            quantity = row["ScaledQuantity"]
            ingredient = row["Ingredient"]
            unit = row["Unit"]
            lines.append(f"{quantity} {unit} {ingredient}")
        sections[category] = lines
    return sections

class PDFThreeColumns(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Catering Companion - Shopping List", ln=True, align="C")
        self.ln(5)

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.set_text_color(0)
        self.cell(0, 8, title, ln=True, align="L")
        self.ln(2)

    def chapter_body(self, lines):
        self.set_font("Arial", "", 10)
        self.set_text_color(50)
        column_width = 60
        line_height = 7
        count = 0
        for line in lines:
            if line.strip():
                x = self.get_x()
                y = self.get_y()
                self.rect(x, y + 1.5, 3.5, 3.5)
                self.cell(7)
                try:
                    parts = line.strip().split(' ', 2)
                    qty = float(parts[0])
                    unit = parts[1]
                    item = parts[2]
                    if qty.is_integer():
                        qty_display = f"{int(qty)}"
                    else:
                        qty_display = f"{qty}"
                    self.cell(column_width - 7, line_height, f"{qty_display} {unit} {item}", ln=0)
                except:
                    self.cell(column_width - 7, line_height, line.strip(), ln=0)

                count += 1
                if count % 3 == 0:
                    self.ln(line_height)
                else:
                    self.set_xy(x + column_width, y)
        self.ln(8)

class PDFRecipeGuides(FPDF):
    def consolidate_unit(self, qty, unit):
        qty = float(qty)
        new_unit = unit.lower()
        if new_unit == 'g' and qty >= 1000:
            return qty / 1000, 'kg'
        elif new_unit == 'ml' and qty >= 1000:
            return qty / 1000, 'l'
        elif new_unit == 'oz' and qty >= 16:
            return qty / 16, 'lb'
        elif new_unit == 'cups' and qty >= 4:
            return qty / 4, 'quarts'
        elif new_unit == 'cups' and qty >= 2:
            return qty / 2, 'pints'
        elif new_unit == 'tsp' and qty >= 3:
            return qty / 3, 'tbsp'
        elif new_unit == 'tbsp' and qty >= 2:
            return qty / 2, 'oz'
        elif new_unit == 'oz' and qty >= 32:
            return qty / 32, 'quarts'
        elif new_unit == 'oz' and qty >= 128:
            return qty / 128, 'gallons'
        else:
            return qty, unit

    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Catering Companion - Recipe Guide", ln=True, align="C")
        self.ln(5)

    def recipe_title(self, title):
        self.set_font("Arial", "B", 16)
        self.set_text_color(0)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(8)

    def recipe_ingredients(self, ingredients):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Ingredients:', ln=True, align='L')
        self.set_font('Arial', '', 11)
        for qty, unit, item in ingredients:
            qty_display, new_unit = self.consolidate_unit(qty, unit)
            if float(qty_display).is_integer():
                qty_display = int(qty_display)
            self.cell(0, 8, f"- {qty_display} {new_unit} {item}", ln=True)
        self.ln(5)
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Ingredients:", ln=True, align="L")
        self.set_font("Arial", "", 11)
        for line in ingredients:
            self.cell(0, 8, f"- {line}", ln=True)
        self.ln(5)

    def recipe_method(self, method_text):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Method:", ln=True, align="L")
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 8, method_text)
        self.ln(5)

def generate_shopping_list_pdf(shopping_sections):
    pdf = PDFThreeColumns()
    pdf.add_page()
    for category, lines in shopping_sections.items():
        pdf.chapter_title(f"Ingredients - {category}")
        pdf.chapter_body(lines)
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    return temp_pdf.name

def generate_recipe_guides_pdf(recipe_guides):
    pdf = PDFRecipeGuides()
    pdf.set_auto_page_break(auto=True, margin=15)
    for recipe_name, (ingredients_list, method_text) in recipe_guides.items():
        pdf.add_page()
        pdf.recipe_title(recipe_name)
        pdf.recipe_ingredients(ingredients_list)
        pdf.recipe_method(method_text)
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    return temp_pdf.name

# Streamlit App Configuration
st.set_page_config(page_title="Catering Companion", page_icon="🍴", layout="centered")

# Custom background
st.markdown(
    """
    <style>
    body {
        background-color: #1e1e1e;
        background-image: url('https://www.transparenttextures.com/patterns/chefskitchen.png');
        background-size: 300px;
        background-repeat: repeat;
        color: white;
    }
    textarea, input, .stTextInput>div>div>input {
        background-color: #333333;
        color: white;
    }
    .css-1d391kg {padding-top: 2rem;}
    .reportview-container {background: #1e1e1e; color: white;}
    #MainMenu, header, footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🍴 Catering Companion")

try:
    recipes_df = pd.read_csv('master_recipe_template.csv')
    available_recipes = recipes_df["RecipeName"].unique()

    user_input = st.text_input("Type your request (e.g., Meatballs, Caesar Salad for 300 people):")

    if st.button("Generate Plan"):
        if user_input.strip() != "":
            st.write("✨ " + random.choice(affirmations))
            with st.spinner('Thinking...'):
                time.sleep(2)  # Simulate thinking time

                input_lower = user_input.lower()
                guest_number = 10
                for word in input_lower.split():
                    if word.isdigit():
                        guest_number = int(word)

                selected_recipes = []
                for recipe in available_recipes:
                    if recipe.lower() in input_lower:
                        selected_recipes.append(recipe)

                if not selected_recipes:
                    st.warning("No matching recipes found. Please check spelling or add recipes to your master list.")
                else:
                    combined_scaled = pd.DataFrame()
                    individual_recipes_scaled = {}
                    methods = {}

                    for recipe_name in selected_recipes:
                        recipe_data = recipes_df[recipes_df["RecipeName"] == recipe_name]
                        scaled_recipe = scale_recipe(recipe_data, guest_number)
                        combined_scaled = pd.concat([combined_scaled, scaled_recipe], ignore_index=True)
                        individual_recipes_scaled[recipe_name] = scaled_recipe
                        methods[recipe_name] = recipe_data["Method"].iloc[0]

                    combined_scaled = combined_scaled.groupby(
                        ["Ingredient", "Unit", "Category"], as_index=False
                    ).sum()

                    shopping_sections = format_shopping_list(combined_scaled)
                    recipe_guides = {}

                    for recipe_name, scaled_data in individual_recipes_scaled.items():
                        ingredients_list = []
                        for _, row in scaled_data.sort_values("Ingredient").iterrows():
                            qty = row["ScaledQuantity"]
                            unit = row["Unit"]
                            ingredient = row["Ingredient"]
                            if qty.is_integer():
                                ingredients_list.append(f"{int(qty)} {unit} {ingredient}")
                            else:
                                ingredients_list.append(f"{qty} {unit} {ingredient}")
                        recipe_guides[recipe_name] = (ingredients_list, methods[recipe_name])

                    shopping_pdf_path = generate_shopping_list_pdf(shopping_sections)
                    recipes_pdf_path = generate_recipe_guides_pdf(recipe_guides)

                    with open(shopping_pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Shopping List as PDF",
                            data=f,
                            file_name="shopping_list.pdf",
                            mime="application/pdf"
                        )

                    with open(recipes_pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Recipe Guides as PDF",
                            data=f,
                            file_name="recipe_guides.pdf",
                            mime="application/pdf"
                        )

except FileNotFoundError:
    st.error("Master recipe file not found. Please make sure 'master_recipe_template.csv' is placed in the same folder as this app.")
