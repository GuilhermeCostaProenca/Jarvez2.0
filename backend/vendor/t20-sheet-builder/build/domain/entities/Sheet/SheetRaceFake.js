"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetRaceFake = void 0;
class SheetRaceFake {
    constructor(race = undefined) {
        this.race = race;
        this.chooseRace = vi.fn();
    }
    getRace() {
        return this.race;
    }
}
exports.SheetRaceFake = SheetRaceFake;
