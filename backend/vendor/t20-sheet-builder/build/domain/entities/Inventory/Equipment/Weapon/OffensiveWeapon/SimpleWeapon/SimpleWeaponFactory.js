"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SimpleWeaponFactory = void 0;
const SimpleWeapons_1 = require("./SimpleWeapons");
class SimpleWeaponFactory {
    static makeFromSerialized(serialized) {
        return new (SimpleWeapons_1.SimpleWeapons.getByName(serialized.name))();
    }
}
exports.SimpleWeaponFactory = SimpleWeaponFactory;
