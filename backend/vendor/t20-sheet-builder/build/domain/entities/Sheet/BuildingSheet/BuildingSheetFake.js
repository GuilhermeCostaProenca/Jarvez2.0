"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BuildingSheetFake = void 0;
const BuildingSheet_1 = require("./BuildingSheet");
class BuildingSheetFake extends BuildingSheet_1.BuildingSheet {
    setLevel(level) {
        this.level = level;
    }
}
exports.BuildingSheetFake = BuildingSheetFake;
