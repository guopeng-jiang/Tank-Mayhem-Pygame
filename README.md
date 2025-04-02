# Tank Mayhem (Pygame)

A classic top-down 2D tank shooter game 100% built using Gemini 2.5 Pro with Python and the Pygame library. Control your tank, blast varied enemies, collect ammo power-ups, and survive the mayhem in randomly generated arenas!

Hello from the pygame community. https://www.pygame.org/contribute.html

## Features

*   **Player Control:** Smooth WASD movement and intuitive mouse-based aiming/turret rotation.
*   **Varied Enemies:** Encounter small, medium, and large enemy tanks, each with different sizes, health, speed, damage, and score values.
*   **Shooting Mechanics:** Limited ammo (21 bullets) adds a strategic element.
*   **Health System:** Both player and enemy tanks have health points. Player takes different damage based on the enemy type.
*   **Randomly Generated Levels:** Each playthrough features a unique layout of barriers.
*   **Ammo Power-up:** Collect the yellow star that appears periodically to instantly refill your ammo!
*   **Scoring:** Earn points for destroying enemy tanks.
*   **Explosion Effects:** Simple particle explosions add visual feedback when bullets hit targets or walls.
*   **Basic Enemy AI:** Enemies move randomly, attempt to avoid obstacles, and only fire when aiming towards the player.
*   **Clear UI:** Displays Score, Player Health, and Player Ammo.
*   **Win/Loss Conditions:** Game ends when all enemies are destroyed (Win) or the player's health reaches zero (Game Over).

## Requirements

*   **Python 3.10**
*   **Pygame Library**

## Installation

1.  **Install Python:** If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/). Make sure to check the option "Add Python to PATH" during installation (or configure it manually).
2.  **Install Pygame:** Open your terminal or command prompt and run:
    ```bash
    pip install pygame
    ```

## How to Run

1.  Save the game code as a Python file (e.g., `tank_game.py`).
2.  Save this README text as `README.md` in the same directory.
3.  Open your terminal or command prompt.
4.  Navigate (`cd`) to the directory where you saved the file(s).
5.  Run the game using the command:
    ```bash
    python tank_game.py
    ```
    (Replace `tank_game.py` if you named your file differently).

## Gameplay & Controls

*   **Goal:** Destroy all enemy tanks before they destroy you!
*   **Movement:**
    *   `W`: Move Up
    *   `A`: Move Left
    *   `S`: Move Down
    *   `D`: Move Right
*   **Aiming:** Move your **Mouse Cursor** to aim the tank's turret.
*   **Shooting:** Click the **Left Mouse Button** to fire a bullet. You have limited ammo!
*   **Power-up:** Drive over the **Yellow Star** when it appears to instantly refill your ammo to the maximum. A new star appears 30 seconds after the previous one was collected.
*   **Enemies:** Different colored tanks have different health and deal different damage. Learn which ones are tougher!
*   **UI:** Keep an eye on your Score, Health (HP), and Ammo in the top-left corner.
*   **Restart (Current):** Press `R` on the Game Over or Win screen to quit the game (a full restart within the game is not yet implemented). Press `Q` to quit from the end screen.

## Future Ideas / Known Issues

*   **Sound Effects:** Add sounds for shooting, explosions, tank movement, power-up collection, etc.
*   **Improved AI:** Make enemies navigate more intelligently or use flanking tactics.
*   **More Power-ups:** Health packs, temporary shields, faster firing rate, etc.
*   **Levels/Waves:** Introduce increasing difficulty or different level objectives.
*   **Collision Response:** Tank collision with walls is basic and tanks can sometimes get stuck briefly.
