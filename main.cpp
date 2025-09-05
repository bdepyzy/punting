#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include <iostream>
#include <string>
#include <utility>

#include "main.h"           //  contains Coord, PLAYER_COORDS, PLAYER_COUNT

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

constexpr int CROP_W = 62; //
constexpr int CROP_H = 85;
constexpr int CROP_COMMUNITY_W = 80;
constexpr int CROP_COMMUNITY_H = 111;

// grab a tiny rectangle into an XImage *
XImage* grab(Display* d, Window root, int x, int y, int w, int h)
{
    return XGetImage(d, root, x, y, w, h, AllPlanes, ZPixmap);
}

// swap B ↔ R in-place (BGRA → RGBA)
inline void bgra_to_rgba(unsigned char* data, std::size_t pixels)
{
    for (std::size_t i = 0; i < pixels; ++i, data += 4)
        std::swap(data[0], data[2]);
}

int main()
{
    Display* d = XOpenDisplay(nullptr);
    if (!d) {
        std::cerr << "XOpenDisplay failed\n";
        return 1;
    }
    Window root = DefaultRootWindow(d);

    for (std::size_t i = 0; i < PLAYER_COUNT; ++i) {
        const PlayerCards& p = PLAYER_COORDS[i];
        std::cout << "capturing player " << (i + 1) << '\n';

        // Use different dimensions for community cards (FLOP, TURN, RIVER)
        bool is_community = (i == FLOP || i == TURN || i == RIVER);
        int crop_w = is_community ? CROP_COMMUNITY_W : CROP_W;
        int crop_h = is_community ? CROP_COMMUNITY_H : CROP_H;

        for (std::size_t card_idx = 0; card_idx < p.count; ++card_idx) {
            const CardCoord& card = p.cards[card_idx];
            
            XImage* cardimg = grab(d, root, card.x, card.y, crop_w, crop_h);
            if (!cardimg) continue;

            bgra_to_rgba(reinterpret_cast<unsigned char*>(cardimg->data),
                         crop_w * crop_h);

            std::string fname;
            if (i == PLAYER_1) {
                fname = "player1_card" + std::to_string(card_idx + 1) + ".png";
            } else if (i == FLOP) {
                fname = "flop_card" + std::to_string(card_idx + 1) + ".png";
            } else if (i == TURN) {
                fname = "turn.png";
            } else if (i == RIVER) {
                fname = "river.png";
            }
            stbi_write_png(fname.c_str(), crop_w, crop_h, 4,
                           cardimg->data, crop_w * 4);

            XDestroyImage(cardimg);
        }
    }

    XCloseDisplay(d);
    return 0;
}
