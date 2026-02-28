import { type DiceRoll, type SerializedDiceRoll } from '../Dice/DiceRoll';
import { type RollResult } from '../Dice/RollResult';
import { type RandomInterface } from '../Random';
import { type Attribute } from '../Sheet';
import { SkillName } from '../Skill';
import { type SkillRollResult, type SheetSkill } from '../Skill/SheetSkill';
import { type TranslatableName } from '../Translator';
import type { Critical, SerializedCritical } from './Critical';
export type SerializedAttack = {
    damage: SerializedDiceRoll;
    critical: SerializedCritical;
    name: TranslatableName;
};
export declare class Attack {
    readonly damage: DiceRoll;
    readonly critical: Critical;
    readonly name: TranslatableName;
    constructor(damage: DiceRoll, critical: Critical, name: TranslatableName);
    roll(random: RandomInterface, skill: SheetSkill): {
        damage: RollResult;
        test: SkillRollResult;
    };
    rollDamage(random: RandomInterface): RollResult;
    getTestDefaultSkill(): SkillName;
    getDamageAttribute(): Attribute | undefined;
    getCustomTestAttributes(): Set<Attribute>;
    serialize(): SerializedAttack;
}
