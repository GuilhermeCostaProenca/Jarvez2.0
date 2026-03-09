import { AbilityEffects } from '../../Ability/AbilityEffects';
import { Spell, type SpellType } from '../Spell';
import { SpellCircle } from '../SpellCircle';
import { SpellName } from '../SpellName';
import { SpellSchool } from '../SpellSchool';
import { MentalDaggerDefaultEffect } from './MentalDaggerDefaultEffect';
export declare class MentalDagger extends Spell {
    static circle: SpellCircle;
    static spellName: SpellName;
    static school: SpellSchool;
    static shortDescription: string;
    static spellType: SpellType;
    school: SpellSchool;
    shortDescription: string;
    effects: AbilityEffects<{
        activateable: {
            default: MentalDaggerDefaultEffect;
        };
    }>;
    constructor();
}
