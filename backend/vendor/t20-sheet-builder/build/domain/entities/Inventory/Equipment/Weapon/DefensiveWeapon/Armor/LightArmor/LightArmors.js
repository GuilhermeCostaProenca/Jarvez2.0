"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LightArmors = void 0;
const LeatherArmor_1 = require("./LeatherArmor");
const StuddedLeatherArmor_1 = require("./StuddedLeatherArmor");
class LightArmors {
    static getAll() {
        return Object.values(LightArmors.map);
    }
    static get(name) {
        return LightArmors.map[name];
    }
}
exports.LightArmors = LightArmors;
LightArmors.map = {
    leatherArmor: LeatherArmor_1.LeatherArmor,
    studdedLeather: StuddedLeatherArmor_1.StuddedLeatherArmor,
};
