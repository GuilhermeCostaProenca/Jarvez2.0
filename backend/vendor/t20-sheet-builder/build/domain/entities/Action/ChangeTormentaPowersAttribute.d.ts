import { Action, type ActionSubClassParams } from './Action';
export declare class ChangeTormentaPowersAttribute extends Action<'changeTormentaPowersAttribute'> {
    constructor(params: ActionSubClassParams<'changeTormentaPowersAttribute'>);
    execute(): void;
    getDescription(): string;
}
