"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FireArmWeaponFactory = void 0;
const errors_1 = require("../../../../../../errors");
const EquipmentName_1 = require("../../../EquipmentName");
const Musket_1 = require("./Musket");
const Pistol_1 = require("./Pistol");
class FireArmWeaponFactory {
    static makeFromSerialized(serialized) {
        switch (serialized.name) {
            case EquipmentName_1.EquipmentName.pistol:
                return new Pistol_1.Pistol();
            case EquipmentName_1.EquipmentName.musket:
                return new Musket_1.Musket();
            default:
                throw new errors_1.SheetBuilderError('UNKNOWN_FIREARM_WEAPON');
        }
    }
}
exports.FireArmWeaponFactory = FireArmWeaponFactory;
