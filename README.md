# REST-mafia
This is a Python application for Really Exciting Social Task "Mafia", that allows people to connect and play "Mafia (Werewolf)" game.
Unlike SOA-mafia, it requires registration and supports user profiles.

# Clarifications for rules
- The only roles are civilians (villagers), mafias (werewolves) and a commissar (seer).
- Game starts on the day phase. On the first day it's impossible to execute anyone.
- When voting, person is executed or murdered if and only if more than half of the players vote for him.
- Commissar can only publish information about mafias. When doing so, it will be anonymous.
- Amount of players in each role depend on amount of players. Here is a table that shows possible configurations:
- At night, only mafia can hear other mafia
- Dead people can't talk, but they can listen

| Player count `n` | Commissar count | Mafias count | Civilians count  |
|------------------|-----------------|--------------|------------------|
| 4                | 1               | 1            | 2                |
| 5                | 1               | 1            | 3                |
| 6                | 1               | 2            | 3                |
| `n > 6`          | 1               | `n // 3`     | `n - 1 - n // 3` |

# Reference
Rules are based on [Wikipedia's section of Gameplay](https://en.wikipedia.org/wiki/Mafia_(party_game)#Gameplay)

Based on [soa-mafia](https://github.com/SpeedOfMagic/soa-mafia), which is based on [voice-chat](https://github.com/SpeedOfMagic/voice-chat), which in turn is based on [TomPrograms](https://github.com/TomPrograms) [Python-Voice-Chat](https://github.com/TomPrograms/Python-Voice-Chat) project.

## License
[MIT](https://choosealicense.com/licenses/mit/)
