import { type AbilityEffectsInterface } from '../../../Ability';
import { type Spell } from '../../../Spell/Spell';
import { type SpellSchool } from '../../../Spell/SpellSchool';
import { RoleAbility } from '../../RoleAbility';
export declare class BardSpells extends RoleAbility {
    readonly schools: Set<SpellSchool>;
    readonly spells: Spell[];
    effects: AbilityEffectsInterface;
    constructor(schools: Set<SpellSchool>, spells: Spell[]);
}
