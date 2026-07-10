import csv
import random
from datetime import date, timedelta
from collections import defaultdict

# Heavily expanded, deduplicated pool of Polish first names
FEMALE_FIRST_NAMES = [
    'Anna', 'Maria', 'Katarzyna', 'Małgorzata', 'Agnieszka', 'Barbara', 'Ewa', 'Magdalena', 'Zofia',
    'Krystyna', 'Elżbieta', 'Joanna', 'Marta', 'Aleksandra', 'Dorota', 'Monika', 'Natalia', 'Karolina',
    'Justyna', 'Julia', 'Zuzanna', 'Maja', 'Alicja', 'Weronika', 'Klaudia', 'Patrycja', 'Paulina', 
    'Dominika', 'Martyna', 'Kamila', 'Sylwia', 'Izabela', 'Agata', 'Iwona', 'Beata', 'Kinga', 
    'Olga', 'Emilia', 'Edyta', 'Urszula', 'Renata', 'Sandra', 'Anita', 'Aneta', 'Danuta', 'Halina'
]

MALE_FIRST_NAMES = [
    'Jan', 'Piotr', 'Krzysztof', 'Andrzej', 'Tomasz', 'Paweł', 'Marcin', 'Michał', 'Jakub',
    'Stanisław', 'Marek', 'Łukasz', 'Grzegorz', 'Mateusz', 'Wojciech', 'Mariusz', 'Dariusz', 'Rafał',
    'Kamil', 'Jacek', 'Maciej', 'Adam', 'Robert', 'Sebastian', 'Filip', 'Kacper', 'Szymon', 
    'Antoni', 'Bartek', 'Przemysław', 'Damian', 'Patryk', 'Dominik', 'Artur', 'Daniel', 'Henryk', 
    'Józef', 'Jerzy', 'Stefan', 'Marian', 'Edward', 'Zbigniew', 'Ryszard', 'Roman', 'Jarosław'
]

# Heavily expanded pool of base masculine Polish last names
LAST_NAMES_BASE = [
    'Nowak', 'Kowalski', 'Wiśniewski', 'Wójcik', 'Kowalczyk', 'Kamiński', 'Lewandowski', 'Zieliński', 
    'Szymański', 'Woźniak', 'Dąbrowski', 'Kozłowski', 'Jankowski', 'Mazur', 'Wojciechowski', 
    'Kwiatkowski', 'Krawczyk', 'Kaczmarek', 'Piotrowski', 'Grabowski', 'Pawłowski', 'Michalski', 
    'Zając', 'Król', 'Wieczorek', 'Jabłoński', 'Wróbel', 'Nowicki', 'Majewski', 'Olszewski', 
    'Stępień', 'Malinowski', 'Jaworski', 'Adamczyk', 'Dudek', 'Nowaczyk', 'Sikora', 'Pawlak', 
    'Górecki', 'Witkowski', 'Walczak', 'Baran', 'Rutkowski', 'Michalak', 'Szewczyk', 'Ostrowski', 
    'Tomaszewski', 'Pietrzak', 'Duda', 'Zalewski', 'Andrzejewski', 'Włodarczyk', 'Borkowski', 
    'Maciejewski', 'Sawicki', 'Chmielewski', 'Kubiak', 'Błaszczyk', 'Szczepański', 'Konieczny', 
    'Cieślak', 'Sikorski', 'Gajewski', 'Głowacki', 'Przybylski', 'Krupa', 'Mróz', 'Bednarek', 
    'Lis', 'Wrona', 'Wasilewski', 'Krajewski', 'Zakrzewski', 'Adamski', 'Skiba', 'Chmiel',
    'Kucharski', 'Lisowski', 'Mazurek', 'Wysocki', 'Kaźmierczak', 'Sobczak', 'Podgórski',
    'Szulc', 'Sadowski', 'Janik', 'Krupiński', 'Borek', 'Czarnecki', 'Prokop', 'Kania', 'Góra'
]

def get_random_date(start_date, end_date):
    """Generates a random date between start_date and end_date."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def generate_employee_csv(filename="employees.csv", num_records=30):
    start_dob = date(1985, 1, 1)
    end_dob = date(2006, 12, 31)
    global_start_join = date(2013, 1, 1)
    global_end_join = date(2026, 4, 30)

    headers = ['employee_id', 'full_name', 'date_of_birth', 'date_joined']
    
    # Strict tracking to prevent name clustering/heavy repetition
    used_full_names = set()
    first_name_counts = defaultdict(int)
    last_name_counts = defaultdict(int)
    
    # Caps to mathematically spread the names evenly across 300 rows
    MAX_FIRST_NAME_REPS = 7   # No individual first name can appear more than 7 times
    MAX_LAST_NAME_REPS = 4    # No individual last name can appear more than 4 times

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        
        for i in range(1, num_records + 1):
            emp_id = f"EMP-{i:05d}"
            
            while True:
                gender = random.choice(['F', 'M'])
                
                if gender == 'F':
                    first_name = random.choice(FEMALE_FIRST_NAMES)
                    base_last_name = random.choice(LAST_NAMES_BASE)
                    # Grammar rule application
                    last_name = base_last_name[:-1] + 'a' if base_last_name.endswith('i') else base_last_name
                else:
                    first_name = random.choice(MALE_FIRST_NAMES)
                    base_last_name = random.choice(LAST_NAMES_BASE)
                    last_name = base_last_name
                
                full_name = f"{first_name} {last_name}"
                
                # Check 1: Guarantee absolute full name uniqueness
                if full_name in used_full_names:
                    continue
                
                # Check 2: Enforce the repetition caps on individual name components
                if first_name_counts[first_name] >= MAX_FIRST_NAME_REPS:
                    continue
                if last_name_counts[base_last_name] >= MAX_LAST_NAME_REPS:
                    continue
                
                # If all guardrails pass, lock them in and update trackers
                used_full_names.add(full_name)
                first_name_counts[first_name] += 1
                last_name_counts[base_last_name] += 1
                break
            
            # Generate valid dates (18+ check)
            dob = get_random_date(start_dob, end_dob)
            try:
                eighteenth_birthday = dob.replace(year=dob.year + 18)
            except ValueError:
                eighteenth_birthday = dob + timedelta(days=18*365 + 4)
            
            actual_start_join = max(global_start_join, eighteenth_birthday)
            date_joined = get_random_date(actual_start_join, global_end_join)
            
            writer.writerow({
                'employee_id': emp_id,
                'full_name': full_name,
                'date_of_birth': dob.strftime('%Y-%m-%d'),
                'date_joined': date_joined.strftime('%Y-%m-%d')
            })

    print(f"Successfully generated {num_records} highly diversified records in '{filename}'.")

if __name__ == "__main__":
    generate_employee_csv("employees.csv", 30)