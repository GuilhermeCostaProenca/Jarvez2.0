import { AbilityEffects } from '../../Ability/AbilityEffects';
import { Spell, type SpellType } from '../Spell';
import { SpellCircle } from '../SpellCircle';
import { SpellName } from '../SpellName';
import { SpellSchool } from '../SpellSchool';
import { FlamesExplosionDefaultEffect } from './FlamesExplosionDefaultEffect';
export declare class FlamesExplosion extends Spell {
    static circle: SpellCircle;
    static school: SpellSchool;
    static spellName: SpellName;
    static shortDescription: string;
    static spellType: SpellType;
    shortDescription: string;
    effects: AbilityEffects<{
        activateable: {
            default: FlamesExplosionDefaultEffect;
        };
    }>;
    school: SpellSchool;
    constructor();
}
