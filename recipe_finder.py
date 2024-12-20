"""
Recipe Finder Application - A comprehensive recipe search tool using the Spoonacular API.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import requests
from typing import List, Dict, Any
from dataclasses import dataclass

# Configuration
API_KEY = "18a2ecb585a34faf967085490068e5d5"
BASE_URL = "https://api.spoonacular.com"

# UI Constants
WINDOW_SIZE = "800x600"
PADDING = 20
FONT_FAMILY = "Helvetica"
PRIMARY_COLOR = "#2196F3"
SECONDARY_COLOR = "#4CAF50"
BACKGROUND_COLOR = "#F5F5F5"
TEXT_COLOR = "#212121"
ERROR_COLOR = "#F44336"

# Fonts
TITLE_FONT = (FONT_FAMILY, 24, "bold")
HEADER_FONT = (FONT_FAMILY, 16, "bold")
NORMAL_FONT = (FONT_FAMILY, 12)
SMALL_FONT = (FONT_FAMILY, 10)

@dataclass
class Recipe:
    id: int
    title: str
    used_ingredients: List[str]
    missed_ingredients: List[str]
    
    @property
    def spoonacular_url(self) -> str:
        formatted_title = self.title.replace(' ', '-').lower()
        return f"https://spoonacular.com/recipes/{formatted_title}-{self.id}"
    
    @classmethod
    def from_api_response(cls, data: dict) -> 'Recipe':
        return cls(
            id=data.get('id', 0),
            title=data.get('title', 'No Title'),
            used_ingredients=[i['name'] for i in data.get('usedIngredients', [])],
            missed_ingredients=[i['name'] for i in data.get('missedIngredients', [])]
        )

class RecipeService:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_key = API_KEY

    def find_recipes_by_ingredients(self, ingredients: str, limit: int = 5) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/recipes/findByIngredients"
        params = {
            "ingredients": ingredients,
            "number": limit,
            "ranking": 2,
            "ignorePantry": True,
            "apiKey": self.api_key
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_recipe_details(self, recipe_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/recipes/{recipe_id}/information"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_recipe_instructions(self, recipe_id: int) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/recipes/{recipe_id}/analyzedInstructions"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

class FavoritesService:
    def __init__(self):
        self.favorites_file = Path.home() / ".recipe_finder_favorites.json"
        self.favorites = self._load_favorites()

    def _load_favorites(self):
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_favorites(self):
        with open(self.favorites_file, 'w') as f:
            json.dump(self.favorites, f)

    def add_favorite(self, recipe_id, recipe_data):
        self.favorites[str(recipe_id)] = recipe_data
        self._save_favorites()

    def remove_favorite(self, recipe_id):
        self.favorites.pop(str(recipe_id), None)
        self._save_favorites()

    def is_favorite(self, recipe_id):
        return str(recipe_id) in self.favorites

class RecipeDetailWindow(tk.Toplevel):
    def __init__(self, parent, recipe_data, recipe_service):
        super().__init__(parent)
        self.recipe_data = recipe_data
        self.recipe_service = recipe_service
        
        self.title(recipe_data["title"])
        self.geometry("600x800")
        self.configure(bg=BACKGROUND_COLOR)
        
        self._create_widgets()
        self._load_recipe_details()

    def _create_widgets(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=PADDING, pady=PADDING)

        canvas = tk.Canvas(container, bg=BACKGROUND_COLOR)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        ttk.Label(
            self.scrollable_frame,
            text=self.recipe_data["title"],
            font=TITLE_FONT,
            wraplength=550
        ).pack(pady=(0, PADDING))

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=550)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

    def _load_recipe_details(self):
        try:
            details = self.recipe_service.get_recipe_details(self.recipe_data["id"])
            instructions = self.recipe_service.get_recipe_instructions(self.recipe_data["id"])

            # Display recipe information
            info_frame = ttk.Frame(self.scrollable_frame)
            info_frame.pack(fill="x", pady=PADDING)

            # Time and servings
            time = details.get("readyInMinutes", "N/A")
            servings = details.get("servings", "N/A")
            
            ttk.Label(
                info_frame,
                text=f"🕒 {time} minutes",
                font=NORMAL_FONT
            ).pack(side="left", padx=5)
            
            ttk.Label(
                info_frame,
                text=f"👥 Serves {servings}",
                font=NORMAL_FONT
            ).pack(side="left", padx=5)

            # Ingredients
            ttk.Label(
                self.scrollable_frame,
                text="Ingredients",
                font=HEADER_FONT
            ).pack(pady=(PADDING, 5))

            for ingredient in details.get("extendedIngredients", []):
                ttk.Label(
                    self.scrollable_frame,
                    text=f"• {ingredient.get('original')}",
                    font=NORMAL_FONT,
                    wraplength=500
                ).pack(anchor="w")

            # Instructions
            ttk.Label(
                self.scrollable_frame,
                text="Instructions",
                font=HEADER_FONT
            ).pack(pady=(PADDING, 5))

            for idx, step in enumerate(instructions[0].get("steps", []), 1):
                step_frame = ttk.Frame(self.scrollable_frame)
                step_frame.pack(fill="x", pady=5)

                ttk.Label(
                    step_frame,
                    text=f"{idx}.",
                    font=NORMAL_FONT
                ).pack(side="left", padx=(0, 5))

                ttk.Label(
                    step_frame,
                    text=step.get("step", ""),
                    font=NORMAL_FONT,
                    wraplength=500
                ).pack(side="left", fill="x")

        except Exception as e:
            ttk.Label(
                self.scrollable_frame,
                text=f"Error loading recipe details: {str(e)}",
                font=NORMAL_FONT,
                foreground=ERROR_COLOR
            ).pack(pady=PADDING)

class RecipeCard(tk.Frame):
    def __init__(self, master, recipe, recipe_service, favorites_service):
        super().__init__(master, bg="white", relief=tk.RAISED, bd=1)
        self.recipe = recipe
        self.recipe_service = recipe_service
        self.favorites_service = favorites_service
        self._create_widgets()

    def _create_widgets(self):
        # Title and favorite button
        header_frame = tk.Frame(self, bg="white")
        header_frame.pack(fill="x", padx=PADDING, pady=(PADDING, 5))

        tk.Label(
            header_frame,
            text=self.recipe.title,
            font=HEADER_FONT,
            bg="white",
            fg=PRIMARY_COLOR,
            wraplength=300
        ).pack(side="left")

        self.favorite_btn = tk.Button(
            header_frame,
            text="★" if self.favorites_service.is_favorite(self.recipe.id) else "☆",
            command=self._toggle_favorite,
            font=(FONT_FAMILY, 16),
            bg="white",
            fg=PRIMARY_COLOR if self.favorites_service.is_favorite(self.recipe.id) else TEXT_COLOR,
            bd=0,
            cursor="hand2"
        )
        self.favorite_btn.pack(side="right")

        # Ingredients
        ingredients_frame = tk.Frame(self, bg="white")
        ingredients_frame.pack(fill="x", padx=PADDING)

        if self.recipe.used_ingredients:
            tk.Label(
                ingredients_frame,
                text="✓ Available:",
                font=(FONT_FAMILY, 10, "bold"),
                bg="white",
                fg=SECONDARY_COLOR
            ).pack(anchor="w")
            
            tk.Label(
                ingredients_frame,
                text=", ".join(self.recipe.used_ingredients),
                font=SMALL_FONT,
                bg="white",
                wraplength=300
            ).pack(anchor="w")

        if self.recipe.missed_ingredients:
            tk.Label(
                ingredients_frame,
                text="✗ Missing:",
                font=(FONT_FAMILY, 10, "bold"),
                bg="white",
                fg=ERROR_COLOR
            ).pack(anchor="w", pady=(5, 0))
            
            tk.Label(
                ingredients_frame,
                text=", ".join(self.recipe.missed_ingredients),
                font=SMALL_FONT,
                bg="white",
                wraplength=300
            ).pack(anchor="w")

        # Buttons
        buttons_frame = tk.Frame(self, bg="white")
        buttons_frame.pack(pady=PADDING)

        ttk.Button(
            buttons_frame,
            text="View Details",
            command=self._show_details
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons_frame,
            text="View Online",
            command=self._open_recipe
        ).pack(side="left", padx=5)

    def _toggle_favorite(self):
        recipe_id = self.recipe.id
        if self.favorites_service.is_favorite(recipe_id):
            self.favorites_service.remove_favorite(recipe_id)
            self.favorite_btn.configure(text="☆", fg=TEXT_COLOR)
        else:
            self.favorites_service.add_favorite(recipe_id, self.recipe.__dict__)
            self.favorite_btn.configure(text="★", fg=PRIMARY_COLOR)

    def _show_details(self):
        RecipeDetailWindow(self, self.recipe.__dict__, self.recipe_service)

    def _open_recipe(self):
        import webbrowser
        webbrowser.open(self.recipe.spoonacular_url)

class RecipeFinderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Recipe Finder")
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=BACKGROUND_COLOR)
        
        self.recipe_service = RecipeService()
        self.favorites_service = FavoritesService()
        
        self._create_widgets()

    def _create_widgets(self):
        # Title
        tk.Label(
            self.root,
            text="Recipe Finder",
            font=TITLE_FONT,
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR
        ).pack(pady=PADDING)

        # Search frame
        search_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        search_frame.pack(fill=tk.X, padx=PADDING)

        tk.Label(
            search_frame,
            text="Enter Ingredients:",
            font=HEADER_FONT,
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR
        ).pack(anchor="w")

        # Search entry
        self.search_entry = ttk.Entry(search_frame, font=NORMAL_FONT, width=50)
        self.search_entry.pack(pady=(5, 0), ipady=8)
        self.search_entry.insert(0, "e.g., chicken, rice, tomatoes")
        self.search_entry.bind("<FocusIn>", self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)
        self.search_entry.bind("<Return>", lambda e: self._find_recipes())

        # Search button
        ttk.Button(
            search_frame,
            text="Find Recipes",
            command=self._find_recipes
        ).pack(pady=PADDING)

        # Results container
        self.results_frame = ttk.Frame(self.root)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING, pady=PADDING)

        # Scrollable canvas for results
        self.canvas = tk.Canvas(self.results_frame, bg=BACKGROUND_COLOR)
        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _clear_placeholder(self, event):
        if self.search_entry.get() == "e.g., chicken, rice, tomatoes":
            self.search_entry.delete(0, tk.END)

    def _restore_placeholder(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "e.g., chicken, rice, tomatoes")

    def _find_recipes(self):
        # Clear previous results
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        ingredients = self.search_entry.get().strip()
        if not ingredients or ingredients == "e.g., chicken, rice, tomatoes":
            messagebox.showerror("Error", "Please enter some ingredients!")
            return

        try:
            recipes_data = self.recipe_service.find_recipes_by_ingredients(ingredients)
            recipes = [Recipe.from_api_response(data) for data in recipes_data]

            if not recipes:
                messagebox.showinfo("Info", "No recipes found.")
                return

            for recipe in recipes:
                card = RecipeCard(
                    self.scrollable_frame,
                    recipe,
                    self.recipe_service,
                    self.favorites_service
                )
                card.pack(fill=tk.X, pady=(0, PADDING))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch recipes: {str(e)}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = RecipeFinderApp()
    app.run()