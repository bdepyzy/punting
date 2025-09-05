#include <tesseract/baseapi.h>
#include <leptonica/allheaders.h>

#include <string>
#include <cctype>
#include <iostream>

#include "main.h"

/* -------------------------------- helpers -------------------------------- */
std::string strip(const std::string& inpt)
{
    auto first = inpt.begin();
    auto last  = inpt.end();
    while (first != last && std::isspace(*first)) ++first;
    while (first != last && std::isspace(*(last - 1))) --last;
    return {first, last};
}

/* remove alpha → upscale ×3 → grayscale 8-bit */
static Pix* preprocess(Pix* src)                       // ★
{
    if (!src) return nullptr;

    Pix* noAlpha = pixRemoveAlpha(src);                // drop RGBA → RGB
    Pix* up3     = pixScale(noAlpha, 3.0f, 3.0f);      // 300 % resize
    pixDestroy(&noAlpha);

    Pix* gray = pixConvertRGBToGray(up3, 0.2126f, 0.7152f, 0.0722f);
    pixDestroy(&up3);

    return gray;                                       // caller owns it
}
/* ------------------------------------------------------------------------- */

int main()
{
    /* ---- initialise Tesseract (LSTM-only, PSM 10, whitelist) ---- */
    tesseract::TessBaseAPI api;
     //, tesseract::OEM_LSTM_ONLY)) {
    if (api.Init(nullptr, "eng", tesseract::OEM_LSTM_ONLY)) {              
        std::cerr << "Could not initialise Tesseract LSTM engine\n";
        return 1;
    }
    api.SetPageSegMode(tesseract::PSM_SINGLE_CHAR);                     // ★ PSM-10
    api.SetVariable("tessedit_char_whitelist", "0123456789AJQK");       // ★

    for (std::size_t i = 0; i < PLAYER_COUNT; ++i) {
        const PlayerCards& player_cards = PLAYER_COORDS[i];
        
        std::cout << "Player " << i + 1 << " OCR: ";
        
        for (std::size_t card_idx = 0; card_idx < player_cards.count; ++card_idx) {
            std::string card_fname;
            if (i == PLAYER_1) {
                card_fname = "player1_card" + std::to_string(card_idx + 1) + ".png";
            } else if (i == FLOP) {
                card_fname = "flop_card" + std::to_string(card_idx + 1) + ".png";
            } else if (i == TURN) {
                card_fname = "turn.png";
            } else if (i == RIVER) {
                card_fname = "river.png";
            }
            
            Pix* card_raw = pixRead(card_fname.c_str());
            if (!card_raw) {
                std::cerr << "Failed to read " << card_fname << '\n';
                continue;
            }

            /* --- preprocess card --- */
            Pix* card_processed = preprocess(card_raw);
            pixDestroy(&card_raw);
            if (!card_processed) continue;

            /* --- OCR card --- */
            api.SetImage(card_processed);
            std::string card_text = strip(api.GetUTF8Text());
            
            std::cout << card_text;
            if (card_idx < player_cards.count - 1) {
                std::cout << "  |  ";
            }

            pixDestroy(&card_processed);
        }
        
        std::cout << '\n';
    }

    api.End();
    return 0;
}
