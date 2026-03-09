import { AbilityEffects } from '../../Ability/AbilityEffects';
import { Spell, type SpellType } from '../Spell';
import { SpellCircle } from '../SpellCircle';
import { SpellName } from '../SpellName';
import { SpellSchool } from '../SpellSchool';
import { IllusoryDisguiseDefaultEffect } from './IllusoryDisguiseDefaultEffect';
export declare class IllusoryDisguise extends Spell {
    static spellName: SpellName;
    static circle: SpellCircle;
    static school: SpellSchool;
    static shortDescription: string;
    static spellType: SpellType;
    shortDescription: string;
    effects: AbilityEffects<{
        activateable: {
            default: IllusoryDisguiseDefaultEffect;
        };
    }>;
    school: SpellSchool;
    constructor();
}
