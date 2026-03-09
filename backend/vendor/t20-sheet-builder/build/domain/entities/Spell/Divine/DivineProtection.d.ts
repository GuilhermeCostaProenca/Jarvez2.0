import { AbilityEffects } from '../../Ability';
import { Spell, type SpellType } from '../Spell';
import { SpellCircle } from '../SpellCircle';
import { SpellName } from '../SpellName';
import { SpellSchool } from '../SpellSchool';
export declare class DivineProtection extends Spell {
    static circle: SpellCircle;
    static school: SpellSchool;
    static spellName: SpellName;
    static shortDescription: string;
    static spellType: SpellType;
    school: SpellSchool;
    shortDescription: string;
    effects: AbilityEffects<Partial<import("../../Ability").AbilityEffectsInterface>>;
    constructor();
}
