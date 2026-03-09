"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Origins = void 0;
const Acolyte_1 = require("./Acolyte/Acolyte");
const AnimalsFriend_1 = require("./AnimalsFriend/AnimalsFriend");
const OriginName_1 = require("./OriginName");
class Origins {
    static getAll() {
        return Object.values(Origins.map);
    }
    static getByName(name) {
        return Origins.map[name];
    }
}
exports.Origins = Origins;
Origins.map = {
    [OriginName_1.OriginName.acolyte]: Acolyte_1.Acolyte,
    [OriginName_1.OriginName.animalsFriend]: AnimalsFriend_1.AnimalsFriend,
};
