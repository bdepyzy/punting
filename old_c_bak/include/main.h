#ifndef MAIN_H_
#define MAIN_H_

#include <array>

struct CardCoord {
    int x;
    int y;
};

constexpr std::size_t MAX_CARDS_PER_PLAYER = 3; // Flop has the most cards

struct PlayerCards {
    std::array<CardCoord, MAX_CARDS_PER_PLAYER> cards;
    std::size_t count;
    
    constexpr PlayerCards(std::initializer_list<CardCoord> card_list) 
        : cards{}, count(card_list.size()) {
        std::size_t i = 0;
        for (const auto& card : card_list) {
            cards[i++] = card;
        }
    }
};

enum Player : std::size_t {   // size_t so it indexes arrays directly
    PLAYER_1,
    FLOP,
    TURN,
    RIVER,
    PLAYER_COUNT           
};

constexpr std::array<PlayerCards, PLAYER_COUNT> PLAYER_COORDS = {
    PlayerCards{{CardCoord{144, 156}, CardCoord{210, 156}}},    // PLAYER_1 (2 cards)
    PlayerCards{{CardCoord{536, 406}, CardCoord{624, 407}, CardCoord{714, 407}}}, // FLOP (3 cards)
    PlayerCards{{CardCoord{804, 407}}},                         // TURN (1 card)
    PlayerCards{{CardCoord{894, 407}}}                          // RIVER (1 card)
};

#endif // MAIN_H_
