"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExoticWeaponFactory = void 0;
const errors_1 = require("../../../../../../errors");
const EquipmentName_1 = require("../../../EquipmentName");
const BastardSword_1 = require("./BastardSword");
const ChainofThorns_1 = require("./ChainofThorns");
const DwarfAxe_1 = require("./DwarfAxe");
const Katana_1 = require("./Katana");
const TauricAxe_1 = require("./TauricAxe");
const Whip_1 = require("./Whip");
class ExoticWeaponFactory {
    static makeFromSerialized(serialized) {
        switch (serialized.name) {
            case EquipmentName_1.EquipmentName.whip:
                return new Whip_1.Whip();
            case EquipmentName_1.EquipmentName.bastardSword:
                return new BastardSword_1.BastardSword();
            case EquipmentName_1.EquipmentName.katana:
                return new Katana_1.Katana();
            case EquipmentName_1.EquipmentName.dwarfAxe:
                return new DwarfAxe_1.DwarfAxe();
            case EquipmentName_1.EquipmentName.chainofThorns:
                return new ChainofThorns_1.ChainofThorns();
            case EquipmentName_1.EquipmentName.tauricAxe:
                return new TauricAxe_1.TauricAxe();
            default:
                throw new errors_1.SheetBuilderError('UNKNOWN_EXOTIC_WEAPON');
        }
    }
}
exports.ExoticWeaponFactory = ExoticWeaponFactory;
