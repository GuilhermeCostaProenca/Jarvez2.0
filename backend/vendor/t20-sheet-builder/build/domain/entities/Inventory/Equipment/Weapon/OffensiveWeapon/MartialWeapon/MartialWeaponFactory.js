"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MartialWeaponFactory = void 0;
const MartialWeapons_1 = require("./MartialWeapons");
class MartialWeaponFactory {
    static makeFromSerialized(serialized) {
        return new (MartialWeapons_1.MartialWeapons.getByName(serialized.name))();
    }
}
exports.MartialWeaponFactory = MartialWeaponFactory;
