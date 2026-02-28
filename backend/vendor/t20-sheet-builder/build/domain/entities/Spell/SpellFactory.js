"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpellFactory = void 0;
const ArcaneArmor_1 = require("./ArcaneArmor/ArcaneArmor");
const ControlPlants_1 = require("./ControlPlants/ControlPlants");
const CureWounds_1 = require("./Divine/CureWounds");
const DivineProtection_1 = require("./Divine/DivineProtection");
const FaithShield_1 = require("./Divine/FaithShield");
const MagicWeapon_1 = require("./Divine/MagicWeapon");
const FlamesExplosion_1 = require("./FlamesExplosion/FlamesExplosion");
const IllusoryDisguise_1 = require("./IllusoryDisguise/IllusoryDisguise");
const MentalDagger_1 = require("./MentalDagger/MentalDagger");
class SpellFactory {
    static make(name) {
        // eslint-disable-next-line @typescript-eslint/naming-convention
        const SpellClass = SpellFactory.map[name];
        return new SpellClass();
    }
}
exports.SpellFactory = SpellFactory;
SpellFactory.map = {
    arcaneArmor: ArcaneArmor_1.ArcaneArmor,
    flamesExplosion: FlamesExplosion_1.FlamesExplosion,
    illusoryDisguise: IllusoryDisguise_1.IllusoryDisguise,
    mentalDagger: MentalDagger_1.MentalDagger,
    controlPlants: ControlPlants_1.ControlPlants,
    cureWounds: CureWounds_1.CureWounds,
    divineProtection: DivineProtection_1.DivineProtection,
    faithShield: FaithShield_1.FaithShield,
    magicWeapon: MagicWeapon_1.MagicWeapon,
};
