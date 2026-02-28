import { PassiveEffect } from '../../../Ability';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
import { type RoleAbilityName } from '../../RoleAbilityName';
export declare class FaithfulDevoteEffect extends PassiveEffect {
    static description: {
        cleric: string;
        druid: string;
    };
    description: string;
    constructor(role: 'cleric' | 'druid', name: RoleAbilityName.clericFaithfulDevote | RoleAbilityName.druidFaithfulDevote);
    apply(transaction: TransactionInterface): void;
}
