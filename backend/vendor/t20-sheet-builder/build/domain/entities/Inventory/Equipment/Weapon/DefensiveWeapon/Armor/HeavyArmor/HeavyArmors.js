"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HeavyArmors = void 0;
const ChainMail_1 = require("./ChainMail");
const FullPlate_1 = require("./FullPlate");
class HeavyArmors {
    static getAll() {
        return Object.values(HeavyArmors.map);
    }
    static get(name) {
        return HeavyArmors.map[name];
    }
}
exports.HeavyArmors = HeavyArmors;
HeavyArmors.map = {
    fullPlate: FullPlate_1.FullPlate,
    chainMail: ChainMail_1.ChainMail,
};
