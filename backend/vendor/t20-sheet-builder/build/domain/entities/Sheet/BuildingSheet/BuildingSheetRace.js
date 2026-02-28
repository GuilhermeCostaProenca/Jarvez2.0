"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BuildingSheetRace = void 0;
class BuildingSheetRace {
    constructor(race = undefined) {
        this.race = race;
    }
    chooseRace(race, transaction) {
        this.race = race;
        this.race.addToSheet(transaction);
    }
    getRace() {
        return this.race;
    }
}
exports.BuildingSheetRace = BuildingSheetRace;
