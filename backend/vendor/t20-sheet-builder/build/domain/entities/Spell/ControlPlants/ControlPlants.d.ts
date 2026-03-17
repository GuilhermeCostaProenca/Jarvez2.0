import { Spell, type SpellType } from '../Spell';
import { SpellCircle } from '../SpellCircle';
import { SpellName } from '../SpellName';
import { SpellSchool } from '../SpellSchool';
import { AbilityEffects } from '../../Ability';
import { ControlPlantsDefaultEffect } from './ControlPlantsDefaultEffect';
export declare class ControlPlants extends Spell {
    static readonly circle = SpellCircle.first;
    static readonly school = SpellSchool.transmutation;
    static readonly spellName = SpellName.controlPlants;
    static spellType: SpellType;
    static get shortDescription(): string;
    school: SpellSchool;
    shortDescription: string;
    effects: AbilityEffects<{
        activateable: {
            default: ControlPlantsDefaultEffect;
        };
    }>;
    constructor();
}
