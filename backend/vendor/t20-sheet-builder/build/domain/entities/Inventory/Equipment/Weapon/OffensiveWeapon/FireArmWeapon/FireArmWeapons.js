"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FireArmWeapons = void 0;
const Musket_1 = require("./Musket");
const Pistol_1 = require("./Pistol");
class FireArmWeapons {
    static getAll() {
        return Object.values(this.map);
    }
    static getByName(name) {
        return this.map[name];
    }
}
exports.FireArmWeapons = FireArmWeapons;
FireArmWeapons.map = {
    pistol: Pistol_1.Pistol,
    musket: Musket_1.Musket,
};
