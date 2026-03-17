"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GeneralPowerFactory = void 0;
const Dodge_1 = require("./CombatPower/Dodge/Dodge");
const FightStyle_1 = require("./CombatPower/FightStyle");
const IronWill_1 = require("./DestinyPower/IronWill/IronWill");
const Medicine_1 = require("./DestinyPower/Medicine/Medicine");
const TormentaPower_1 = require("./TormentaPower");
class GeneralPowerFactory {
    static make(params) {
        return new GeneralPowerFactory.generalPowerClasses[params.name]();
    }
}
exports.GeneralPowerFactory = GeneralPowerFactory;
GeneralPowerFactory.generalPowerClasses = {
    dodge: Dodge_1.Dodge,
    ironWill: IronWill_1.IronWill,
    medicine: Medicine_1.Medicine,
    oneWeaponStyle: FightStyle_1.OneWeaponStyle,
    shell: TormentaPower_1.Shell,
};
