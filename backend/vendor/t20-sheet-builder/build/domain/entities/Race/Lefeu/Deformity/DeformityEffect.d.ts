import { PassiveEffect } from '../../../Ability/PassiveEffect';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
import { type SkillName } from '../../../Skill';
export declare class DeformityEffect extends PassiveEffect {
    get description(): string;
    readonly choices: SkillName[];
    constructor();
    addChoice(newChoice: SkillName): void;
    apply(transaction: TransactionInterface): void;
}
