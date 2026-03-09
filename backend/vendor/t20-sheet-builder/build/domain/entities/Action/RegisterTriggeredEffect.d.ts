import { Action, type ActionSubClassParams } from './Action';
export declare class RegisterTriggeredEffect extends Action<'registerTriggeredEffect'> {
    constructor(params: ActionSubClassParams<'registerTriggeredEffect'>);
    execute(): void;
    getDescription(): string;
}
