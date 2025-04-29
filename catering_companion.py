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

class PDFCheckboxPerfect(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Catering Companion - Shopping List", ln=True, align="C")
        self.ln(5)

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.set_text_color(0)
        self.cell(0, 10, title, ln=True, align="L")
        self.ln(2)

    def chapter_body(self, lines):
        self.set_font("Arial", "", 11)
        self.set_text_color(50)
        for line in lines:
            if line.strip():
                self.rect(self.get_x(), self.get_y() + 1.5, 4, 4)
                self.cell(8)
                try:
                    parts = line.strip().split(' ', 2)
                    qty = float(parts[0])
                    unit = parts[1]
                    item = parts[2]
                    if qty.is_integer():
                        qty_display = f"{int(qty)}"
                    else:
                        qty_display = f"{qty}"
                    self.cell(0, 8, f"{qty_display} {unit} {item}", ln=True)
                except:
                    self.cell(0, 8, line.strip(), ln=True)
        self.ln()

def generate_pdf(shopping_sections):
    pdf = PDFCheckboxPerfect()
    pdf.add_page()
    for category, lines in shopping_sections.items():
        pdf.chapter_title(f"Ingredients - {category}")
        pdf.chapter_body(lines)
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
                    pdf_file_path = generate_pdf(shopping_sections)

                    with open(pdf_file_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Shopping List as PDF",
                            data=f,
                            file_name="shopping_list.pdf",
                            mime="application/pdf"
                        )

                    st.markdown("---")
                    st.markdown("# 📃 Recipe Methods")
                    for recipe_name, scaled_data in individual_recipes_scaled.items():
                        st.markdown(f"## {recipe_name}")
                        st.markdown("### Ingredients:")
                        for _, row in scaled_data.sort_values("Ingredient").iterrows():
                            qty = row["ScaledQuantity"]
                            unit = row["Unit"]
                            ingredient = row["Ingredient"]
                            if qty.is_integer():
                                st.markdown(f"- {int(qty)} {unit} {ingredient}")
                            else:
                                st.markdown(f"- {qty} {unit} {ingredient}")
                        st.markdown("### Method:")
                        st.markdown(methods[recipe_name])
                        st.markdown('<div style="page-break-after: always;"></div>', unsafe_allow_html=True)
except FileNotFoundError:
    st.error("Master recipe file not found. Please make sure 'master_recipe_template.csv' is placed in the same folder as this app.")
