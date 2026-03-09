import { type AbilityEffectsInterface } from '../../../Ability';
import { type SpellName } from '../../../Spell';
import { RaceAbility } from '../../RaceAbility';
export declare class MysticTattoo extends RaceAbility {
    readonly spell: SpellName;
    effects: AbilityEffectsInterface;
    constructor(spell: SpellName);
}
