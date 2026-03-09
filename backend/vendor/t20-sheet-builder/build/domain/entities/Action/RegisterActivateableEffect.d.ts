import { Action, type ActionSubClassParams } from './Action';
export declare class RegisterActivateableEffect extends Action<'registerActivateableEffect'> {
    constructor(params: ActionSubClassParams<'registerActivateableEffect'>);
    execute(): void;
    getDescription(): string;
}
