"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Shell = void 0;
const AbilityEffects_1 = require("../../../../Ability/AbilityEffects");
const AbilityEffectsStatic_1 = require("../../../../Ability/AbilityEffectsStatic");
const GeneralPowerName_1 = require("../../GeneralPowerName");
const TormentaPower_1 = require("../TormentaPower");
const ShellEffect_1 = require("./ShellEffect");
class Shell extends TormentaPower_1.TormentaPower {
    constructor() {
        super(Shell.powerName);
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                default: new ShellEffect_1.ShellEffect(),
            },
        });
    }
}
exports.Shell = Shell;
Shell.powerName = GeneralPowerName_1.GeneralPowerName.shell;
Shell.effects = new AbilityEffectsStatic_1.AbilityEffectsStatic({
    passive: {
        default: ShellEffect_1.ShellEffect,
    },
});
