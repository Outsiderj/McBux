import discord
from discord.ext import commands
import json
import typing
import random
import asyncio

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!', intents=intents)
class_emojis = {
    'Fighter': '🥊',
    'Rogue': '🗡️',
    'Entertainer': '🎭',
    'Spellcaster': '🧙‍♂️'
}

def summarize_messages(messages):
    # Tokenize the messages into sentences
    sentences = [nltk.sent_tokenize(message) for message in messages]
    sentences = [sentence for sublist in sentences for sentence in sublist]  # Flatten the list

    # Create a TF-IDF vectorizer
    vectorizer = TfidfVectorizer().fit_transform(sentences)

    # Sum the TF-IDF scores for each sentence
    sentence_scores = defaultdict(float)
    for i, sentence in enumerate(sentences):
        for j in vectorizer[i].indices:
            sentence_scores[sentence] += vectorizer[i, j]

    # Sort the sentences by their scores
    sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)

    # Take the top N sentences as the summary (e.g., top 5)
    summary_sentences = sorted_sentences[:20]

    # Return the summary as a string
    return "\n".join(summary_sentences)

# Global variable to store captured messages
captured_messages = []

@bot.command()
async def save(ctx, mode: str):
    global save_mode
    global captured_messages

    if mode.lower() == "on":
        save_mode = True
        captured_messages = []  # Reset the captured messages
        await ctx.send("Save mode activated. Capturing all output from the Character.ai bot.")
    elif mode.lower() == "off":
        save_mode = False
        summary = summarize_messages(captured_messages)
        await ctx.send(f"Save mode deactivated. Summary of captured messages:\n{summary}")
    elif mode.lower() == "summary":
        summary = summarize_messages(captured_messages)
        await ctx.send(f"Summary of captured messages:\n{summary}")
    else:
        await ctx.send("Invalid mode. Use '!save on', '!save off', or '!save summary'.")

@bot.event
async def on_message(message):
    global captured_messages

    # Check if the message is from the Character.ai bot and save mode is activated
    if message.author.id == 1118735015472283658 and save_mode:
        captured_messages.append(message.content)

    # Process other bot commands
    await bot.process_commands(message)



class ClassSelection(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60.0)
        self.value = None
        self.author = author

    @discord.ui.button(label='🥊 Fighter', style=discord.ButtonStyle.primary)
    async def fighter(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            self.value = 'Fighter'
            self.stop()

    @discord.ui.button(label='🗡️ Rogue', style=discord.ButtonStyle.primary)
    async def rogue(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            self.value = 'Rogue'
            self.stop()

    @discord.ui.button(label='🎭 Entertainer', style=discord.ButtonStyle.primary)
    async def entertainer(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            self.value = 'Entertainer'
            self.stop()

    @discord.ui.button(label='🧙‍♂️ Spellcaster', style=discord.ButtonStyle.primary)
    async def spellcaster(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            self.value = 'Spellcaster'
            self.stop()

class Decision(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60.0)
        self.value = None
        self.author = author

    @discord.ui.button(label='✅ Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            self.value = True
            self.stop()

    @discord.ui.button(label='❌ Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            self.value = False
            self.stop()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('------')

@bot.command()
async def gen(ctx):
    author = ctx.author

    await author.send('Hello! Please enter your character name (up to 40 characters):')

    def check(m):
        return m.author == author

    try:
        name_msg = await bot.wait_for('message', check=check, timeout=60)
        character_name = name_msg.content[:40]

        class_embed = discord.Embed(title='Class Selection')
        class_embed.add_field(name='Choose your class:', value='1. Fighter\n2. Rogue\n3. Entertainer\n4. Spellcaster')
        class_view = ClassSelection(author)
        await author.send(embed=class_embed, view=class_view)
        await class_view.wait()

        if class_view.value is None:
            await ctx.send('Class selection timed out. Please try again later.')
            return

        character_class = class_view.value
        await author.send(f'You have chosen the class "{character_class}".')

        keep_character = False
        while not keep_character:
            initial_stats = calculate_initial_stats(character_class)

            stats_embed = discord.Embed(title='Initial Stats')
            for stat, value in initial_stats.items():
                stats_embed.add_field(name=stat, value=value)
            stats_message = await author.send(embed=stats_embed)

            decision_view = Decision(author)
            await author.send('Do you want to keep this character?', view=decision_view)
            await decision_view.wait()

            if decision_view.value is None:
                await ctx.send('Character creation timed out. Please try again later.')
                return

            if decision_view.value:
                keep_character = True
                await author.send('Character kept! You have received 50 gold pieces.')

                starting_equipment = get_starting_equipment(character_class)
                await author.send(f'You have received a {starting_equipment["name"]} as your starting weapon.')

                if character_class == 'Spellcaster':
                    await author.send('You have received beginner spells.')
                elif character_class == 'Entertainer':
                    await author.send('You have received beginner songs.')
                elif character_class == 'Fighter':
                    await author.send('You have received a starting skill for fighters.')
                elif character_class == 'Rogue':
                    await author.send('You have received a starting skill for rogues.')

                character_status = 'alive'

                # Save all character data to the JSON file
                data = {
                    'name': character_name,
                    'user_id': author.id,
                    'class': character_class,
                    'stats': initial_stats,
                    'equipment': starting_equipment,
                    'status': character_status
                }
                with open('characters.json', 'r') as file:
                    characters = json.load(file)

                characters.append(data)

                with open('characters.json', 'w') as file:
                    json.dump(characters, file)
            else:
                await stats_message.delete()
                await author.send('Character re-rolled!')

    except asyncio.TimeoutError:
        await ctx.send('Character name input timed out. Please try again later.')


def calculate_initial_stats(character_class):
    stats = {
        'strength': random.randint(6, 18),
        'dexterity': random.randint(6, 18),
        'constitution': random.randint(6, 18),
        'intelligence': random.randint(6, 18),
        'wisdom': random.randint(6, 18),
        'charisma': random.randint(6, 18)
    }

    if character_class == 'Fighter':
        stats['strength'] += 2
        stats['constitution'] += 1
    elif character_class == 'Rogue':
        stats['dexterity'] += 2
        stats['intelligence'] += 1
    elif character_class == 'Entertainer':
        stats['charisma'] += 2
        stats['dexterity'] += 1
    elif character_class == 'Spellcaster':
        stats['intelligence'] += 2
        stats['wisdom'] += 1

    max_hit_points = 10 + stats['constitution']
    stats['max_hit_points'] = max_hit_points
    stats['hit_points'] = max_hit_points
    
    return stats

def get_starting_equipment(character_class):
    equipment = {}

    if character_class == 'Fighter':
        equipment = {'name': 'Sword', 'damage': '1d8'}
    elif character_class == 'Rogue':
        equipment = {'name': 'Dagger', 'damage': '1d4'}
    elif character_class == 'Entertainer':
        equipment = {'name': 'Lute', 'damage': '1d6'}
    elif character_class == 'Spellcaster':
        equipment = {'name': 'Staff', 'damage': '1d6'}

    return equipment

# Global variable to store the active character for the current user
active_character = None

class CharacterSelection(discord.ui.View):
    def __init__(self, author, characters):
        super().__init__(timeout=60.0)
        self.value = None
        self.author = author
        self.characters = characters

    @discord.ui.select(placeholder='Select a Character', min_values=1, max_values=1)
    async def select(self, select: discord.ui.Select, interaction: discord.Interaction):
        if interaction.user == self.author:
            self.value = select.values[0]
            self.stop()

# Define a dictionary mapping classes to their corresponding emojis
class_emojis = {
    'Fighter': '🥊',
    'Rogue': '🗡️',
    'Entertainer': '🎭',
    'Spellcaster': '🧙‍♂️'
}

@bot.command()
async def load(ctx):
    global active_character
    author = ctx.author

    # Load the character data from the JSON file
    with open('characters.json', 'r') as file:
        characters = json.load(file)

    # Filter the characters to only include those associated with the author's Discord ID
    user_characters = [character for character in characters if character['user_id'] == author.id]

    if not user_characters:
        await ctx.send('You have no characters. Use the !gen command to generate a new character.')
        return

    # Mark all characters as inactive
    for character in user_characters:
        character['status'] = 'inactive'

    # Build a list of character names and classes
    character_names_classes = [f"{character['name']} ({character['class']})" for character in user_characters]

    character_view = CharacterSelection(author, user_characters)
    character_view.select.options = [discord.SelectOption(label=name_class) for name_class in character_names_classes]
    await ctx.send('Please select a character:', view=character_view)
    await character_view.wait()

    if character_view.value is None:
        await ctx.send('Character selection timed out. Please try again later.')
        return

    # Mark the selected character as active
    selected_character_name, _ = character_view.value.rsplit(" (", 1)  # Get the character name only, without the class
    for character in user_characters:
        if character['name'] == selected_character_name:
            character['status'] = 'active'
            active_character = character
            break

    # Save the updated character data back to the JSON file
    with open('characters.json', 'w') as file:
        json.dump(characters, file)

    # Get the emoji for the character's class
    class_emoji = class_emojis.get(active_character['class'], '')  # Default to an empty string if the class is not found

    await ctx.send(f'Character "{active_character["name"]}" ({class_emoji}) has been loaded.')


@bot.command()
async def sheet(ctx):
    author = ctx.author

    # Load the character data from the JSON file
    with open('characters.json', 'r') as file:
        characters = json.load(file)

    # Filter the characters to only include the active one associated with the author's Discord ID
    active_characters = [character for character in characters if character['user_id'] == author.id and character['status'] == 'active']

    # Ensure that a character is loaded
    if not active_characters:
        await ctx.send('No character is currently loaded. Use the !load command to load a character.')
        return

    active_character = active_characters[0]  # There should only be one active character per user

    # Create a new embed to display the character sheet
    embed = discord.Embed(title=f"Character Sheet: {active_character['name']}", color=discord.Color.blue())

    # Add field to the embed for the player's class
    if 'class' in active_character:
        embed.add_field(name='Class', value=active_character['class'], inline=True)

    # Add fields to the embed for each stat
    for stat, value in active_character['stats'].items():
        if stat != 'hit_points':
            bonus = ''
            if active_character['class'] == 'Fighter' and stat in ['strength', 'constitution']:
                bonus = ' (+2)' if stat == 'strength' else ' (+1)'
            elif active_character['class'] == 'Rogue' and stat in ['dexterity', 'intelligence']:
                bonus = ' (+2)' if stat == 'dexterity' else ' (+1)'
            elif active_character['class'] == 'Entertainer' and stat in ['charisma', 'dexterity']:
                bonus = ' (+2)' if stat == 'charisma' else ' (+1)'
            elif active_character['class'] == 'Spellcaster' and stat in ['intelligence', 'wisdom']:
                bonus = ' (+2)' if stat == 'intelligence' else ' (+1)'
            embed.add_field(name=stat.capitalize(), value=str(value) + bonus, inline=True)

    # If max_hit_points is not present in stats, use hit_points
    max_hit_points = active_character['stats'].get('max_hit_points', active_character['stats']['hit_points'])

    # Add field for hit points, displayed as [current/max]
    embed.add_field(name='Hit Points', value=f"[{active_character['stats']['hit_points']}/{max_hit_points}]", inline=True)

    # Add fields to the embed for weapon, if it exists
    if 'equipment' in active_character:
        weapon_name = active_character['equipment']['name']
        weapon_damage = active_character['equipment']['damage']
        embed.add_field(name='Weapon', value=f'{weapon_name} (Damage: {weapon_damage})', inline=False)

    # If the character has an inventory field, add it to the embed
    if 'inventory' in active_character:
        inventory = ', '.join(f"{item} x {quantity}" for item, quantity in active_character['inventory'].items())
        embed.add_field(name='Inventory', value=inventory, inline=False)

    # Send the embed to the channel
    await ctx.send(embed=embed)
