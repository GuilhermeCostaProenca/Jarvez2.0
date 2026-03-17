import { Action, type ActionSubClassParams } from './Action';
export declare class ApplyRoleAbility extends Action<'applyRoleAbility'> {
    constructor(params: ActionSubClassParams<'applyRoleAbility'>);
    execute(): void;
    getDescription(): string;
}
