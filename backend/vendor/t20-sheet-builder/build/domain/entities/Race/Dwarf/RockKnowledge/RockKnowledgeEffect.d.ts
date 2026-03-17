import { PassiveEffect } from '../../../Ability/PassiveEffect';
import type { ModifierCondition } from '../../../Modifier/ContextualModifier/ContextualModifiersListInterface';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
export declare class RockKnowledgeEffect extends PassiveEffect {
    get description(): string;
    static readonly condition: ModifierCondition;
    static get skillModifier(): number;
    constructor();
    apply(transaction: TransactionInterface): void;
}
